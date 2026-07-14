import pytest
from datetime import timedelta

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import DailyActivity, ExampleSentence, LearningItem, Lesson, LessonProgress, LessonQuizAttempt, MistakeLog, ReviewLog, User, UserProgress
from app.services.exercise_service import answer_for, build_exercise, select_adaptive_item
from app.services.learning_path_service import build_path_state, next_path_step
from app.services.level_service import level_readiness
from app.services.recommendation_service import recommend_next
from app.services.srs_service import apply_review
from app.models import utcnow
from seed import seed


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def register(client, username="aki", email="aki@example.com", password="secret1"):
    return client.post("/register", data={"username": username, "email": email, "password": password}, follow_redirects=True)


def login(client, identifier="aki", password="secret1"):
    return client.post("/login", data={"identifier": identifier, "password": password}, follow_redirects=True)


def test_app_starts(client):
    assert client.get("/").status_code == 200


def test_user_can_register_and_login(client):
    response = register(client)
    assert response.status_code == 200
    client.get("/logout")
    response = login(client)
    assert b"Dashboard" in response.data or response.status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_seed_data_creates_kana_and_grammar(app):
    with app.app_context():
        seed()
        assert LearningItem.query.filter_by(item_type="kana").count() >= 92
        assert LearningItem.query.filter_by(item_type="grammar").count() >= 15
        assert Lesson.query.count() >= 5
        assert Lesson.query.filter_by(slug="hiragana-foundations").first().items
        assert ExampleSentence.query.count() >= 10


def test_mark_lesson_seen_updates_progress(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        item = LearningItem.query.filter_by(slug="particle-wa").first()
    client.post(f"/learn/{item.slug}", data={"action": "seen"}, follow_redirects=True)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert progress.status == "seen"


def test_structured_lesson_completion_tracks_lesson_and_items(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.post("/lessons/hiragana-foundations", data={"action": "complete"}, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        lesson_progress = LessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        activity = DailyActivity.query.filter_by(user_id=user.id).first()
        assert lesson_progress.status == "completed"
        assert lesson_progress.items_seen == len(lesson.items)
        assert UserProgress.query.filter_by(user_id=user.id).count() >= len(lesson.items)
        assert activity.lessons_completed == 1
        assert activity.xp_earned == lesson.xp_reward
        assert user.streak == 1


def test_lesson_practice_updates_srs_and_lesson_accuracy(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        item = LearningItem.query.filter_by(slug="hiragana-a").first()
    response = client.post(
        "/lessons/hiragana-foundations/practice",
        data={"item_id": item.id, "prompt": item.japanese, "answer": item.reading},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        lesson_progress = LessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        item_progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert lesson_progress.exercises_attempted == 1
        assert lesson_progress.exercises_correct == 1
        assert item_progress.srs_stage == 1


def test_lesson_quiz_renders_generated_exercises(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/lessons/hiragana-foundations/quiz")
    assert response.status_code == 200
    assert b"Submit Quiz" in response.data
    assert b"Type the romaji reading." in response.data


def test_lesson_quiz_submission_records_result_and_reviews(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        data = {}
        for link in lesson.items:
            item = link.learning_item
            data[f"prompt_{item.id}"] = item.japanese
            data[f"answer_{item.id}"] = item.reading
    response = client.post("/lessons/hiragana-foundations/quiz", data=data, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        attempt = LessonQuizAttempt.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        progress = LessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
        activity = DailyActivity.query.filter_by(user_id=user.id).first()
        assert attempt.score_percent == 100
        assert attempt.passed is True
        assert attempt.question_count == len(lesson.items)
        assert ReviewLog.query.filter_by(user_id=user.id, review_type="quiz:hiragana-foundations").count() == len(lesson.items)
        assert progress.status == "completed"
        assert activity.reviews_completed == len(lesson.items)
        assert activity.xp_earned == len(lesson.items) * 10


def test_learning_path_locks_lessons_until_previous_quiz_passes(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        db.session.commit()
        states = build_path_state(user)
        assert states[0]["state"] == "current"
        assert states[1]["state"] == "locked"


def test_learning_path_unlocks_after_passing_previous_lesson(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        data = {}
        for link in lesson.items:
            item = link.learning_item
            data[f"prompt_{item.id}"] = item.japanese
            data[f"answer_{item.id}"] = item.reading
    client.post("/lessons/hiragana-foundations/quiz", data=data, follow_redirects=True)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        states = build_path_state(user)
        assert states[0]["state"] == "completed"
        assert states[1]["state"] == "current"
        assert next_path_step(user)["title"] == "Basic Identity Sentences"


def test_locked_lesson_redirects_to_study_path(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/lessons/basic-identity/practice", follow_redirects=False)
    assert response.status_code == 302
    assert "/study-path" in response.headers["Location"]


def test_recommendation_uses_learning_path_state(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        db.session.commit()
        recommendation = recommend_next(user)
        assert recommendation["title"] == "Hiragana Foundations"
        assert "next lesson" in recommendation["reason"].lower()


def test_weak_practice_empty_state(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/weak-practice")
    assert response.status_code == 200
    assert b"No practice items available." in response.data


def test_weak_practice_uses_unresolved_mistakes(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        item = LearningItem.query.filter_by(slug="hiragana-a").first()
        db.session.add(MistakeLog(user=user, learning_item=item, mistake_text="x", correct_answer=item.reading))
        db.session.commit()
    response = client.get("/weak-practice")
    assert response.status_code == 200
    assert b"Type the romaji reading." in response.data


def test_weak_practice_correct_answer_resolves_related_mistake(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        item = LearningItem.query.filter_by(slug="hiragana-a").first()
        db.session.add(MistakeLog(user=user, learning_item=item, mistake_text="x", correct_answer=item.reading))
        db.session.commit()
        item_id = item.id
    response = client.post(
        "/weak-practice",
        data={"item_id": item_id, "prompt": "あ", "answer": "a"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        item = LearningItem.query.filter_by(id=item_id).first()
        mistake = MistakeLog.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert mistake.resolved is True
        assert progress.correct_count == 1
        assert ReviewLog.query.filter_by(user_id=user.id, review_type="weak").count() == 1


def test_mastery_empty_state(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/mastery")
    assert response.status_code == 200
    assert b"No learned items yet." in response.data


def test_mastery_inventory_lists_learned_and_mastered_items(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        vocab = LearningItem.query.filter_by(slug="vocab-water").first()
        kana = LearningItem.query.filter_by(slug="hiragana-a").first()
        grammar = LearningItem.query.filter_by(slug="particle-wa").first()
        db.session.add(UserProgress(user=user, learning_item=vocab, status="known", mastery_level=3, accuracy=80))
        db.session.add(UserProgress(user=user, learning_item=kana, status="mastered", mastery_level=5, accuracy=100))
        db.session.add(UserProgress(user=user, learning_item=grammar, status="known", mastery_level=3, accuracy=75))
        db.session.commit()
    response = client.get("/mastery")
    assert response.status_code == 200
    assert b"Water" in response.data
    assert b"Hiragana" in response.data
    assert b"Particle" in response.data
    assert b"3 learned" in response.data
    assert b"1 mastered" in response.data


def test_item_lesson_displays_seeded_examples(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/learn/vocab-water")
    assert response.status_code == 200
    assert "水をください。".encode() in response.data
    assert b"Water, please." in response.data


def test_lesson_unit_displays_related_examples_after_unlocked(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/lessons/hiragana-foundations")
    assert response.status_code == 200
    assert b"Lesson Examples" not in response.data
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        lesson = Lesson.query.filter_by(slug="basic-identity").first()
        db.session.add(LessonProgress(user=user, lesson=lesson, status="in_progress"))
        db.session.commit()
    response = client.get("/lessons/basic-identity")
    assert response.status_code == 200
    assert b"Lesson Examples" in response.data
    assert "私は学生です。".encode() in response.data


def test_level_readiness_uses_content_lessons_and_quizzes(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(slug="hiragana-a").first()
        lesson = Lesson.query.filter_by(slug="hiragana-foundations").first()
        db.session.add(UserProgress(user=user, learning_item=item, status="known", mastery_level=3, accuracy=100))
        db.session.add(LessonProgress(user=user, lesson=lesson, status="completed"))
        db.session.add(LessonQuizAttempt(user=user, lesson=lesson, correct_count=5, question_count=5, score_percent=100, passed=True))
        db.session.commit()
        readiness = level_readiness(user)
        assert readiness["readiness"] > 0
        assert readiness["lessons_complete"] == 1
        assert readiness["passed_quizzes"] == 1
        assert any(skill["item_type"] == "kana" and skill["learned"] == 1 for skill in readiness["skills"])


def test_progress_page_renders_level_progression(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/progress")
    assert response.status_code == 200
    assert b"Level Progression" in response.data
    assert b"N5 readiness" in response.data
    assert b"N5 readiness placeholder" not in response.data


def test_dashboard_renders_readiness_label(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Starting N5" in response.data


def test_admin_can_manage_examples(client, app):
    with app.app_context():
        seed()
    register(client, username="admin", email="admin@example.com")
    with app.app_context():
        item = LearningItem.query.filter_by(slug="vocab-water").first()
        item_id = item.id
    response = client.get("/admin/examples")
    assert response.status_code == 200
    assert b"Admin Examples" in response.data

    response = client.post(
        "/admin/examples/new",
        data={
            "learning_item_id": item_id,
            "japanese": "水です。",
            "reading": "みずです。",
            "english": "It is water.",
            "note": "Short example.",
            "difficulty": 1,
            "source_name": "",
            "source_url": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        example = ExampleSentence.query.filter_by(japanese="水です。").first()
        assert example is not None
        example_id = example.id

    response = client.post(
        f"/admin/examples/{example_id}/edit",
        data={
            "learning_item_id": item_id,
            "japanese": "冷たい水です。",
            "reading": "つめたい みずです。",
            "english": "It is cold water.",
            "note": "Updated example.",
            "difficulty": 2,
            "source_name": "",
            "source_url": "",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        example = db.session.get(ExampleSentence, example_id)
        assert example.english == "It is cold water."
        assert example.difficulty == 2

    response = client.post(f"/admin/examples/{example_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(ExampleSentence, example_id) is None


def test_admin_can_manage_lessons_and_ordered_items(client, app):
    with app.app_context():
        seed()
    register(client, username="admin", email="admin@example.com")
    response = client.get("/admin/lessons")
    assert response.status_code == 200
    assert b"Admin Lessons" in response.data

    response = client.post(
        "/admin/lessons/new",
        data={
            "slug": "admin-test-lesson",
            "title": "Admin Test Lesson",
            "description": "Created from admin.",
            "level": "N5",
            "skill_focus": "kana",
            "sequence": 99,
            "xp_reward": 30,
            "item_slugs": "hiragana-a\nhiragana-i",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        lesson = Lesson.query.filter_by(slug="admin-test-lesson").first()
        assert lesson is not None
        assert [link.learning_item.slug for link in lesson.items] == ["hiragana-a", "hiragana-i"]
        lesson_id = lesson.id

    response = client.post(
        f"/admin/lessons/{lesson_id}/edit",
        data={
            "slug": "admin-test-lesson",
            "title": "Updated Admin Lesson",
            "description": "Updated.",
            "level": "N5",
            "skill_focus": "kana",
            "sequence": 100,
            "xp_reward": 40,
            "item_slugs": "hiragana-u, hiragana-e",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        lesson = db.session.get(Lesson, lesson_id)
        assert lesson.title == "Updated Admin Lesson"
        assert lesson.sequence == 100
        assert [link.learning_item.slug for link in lesson.items] == ["hiragana-u", "hiragana-e"]

    response = client.post(f"/admin/lessons/{lesson_id}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert db.session.get(Lesson, lesson_id) is None


def test_review_schedule_groups_due_and_upcoming_items(client, app):
    with app.app_context():
        seed()
    register(client)
    with app.app_context():
        user = User.query.filter_by(username="aki").first()
        due_item = LearningItem.query.filter_by(slug="hiragana-a").first()
        tomorrow_item = LearningItem.query.filter_by(slug="hiragana-i").first()
        later_item = LearningItem.query.filter_by(slug="hiragana-u").first()
        db.session.add(UserProgress(user=user, learning_item=due_item, status="reviewing", mastery_level=2, srs_stage=1, next_review=utcnow() - timedelta(minutes=1)))
        db.session.add(UserProgress(user=user, learning_item=tomorrow_item, status="reviewing", mastery_level=2, srs_stage=2, next_review=utcnow() + timedelta(days=1)))
        db.session.add(UserProgress(user=user, learning_item=later_item, status="reviewing", mastery_level=4, srs_stage=5, next_review=utcnow() + timedelta(days=20)))
        db.session.commit()
    response = client.get("/reviews/schedule")
    assert response.status_code == 200
    assert b"Review Schedule" in response.data
    assert b"Due now" in response.data
    assert b"Tomorrow" in response.data
    assert b"Later" in response.data
    assert b"Hiragana" in response.data


def test_reviews_page_links_to_schedule(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/reviews")
    assert response.status_code == 200
    assert b"Schedule" in response.data


def test_exercise_service_builds_typed_grammar_exercise(app):
    with app.app_context():
        seed()
        grammar = LearningItem.query.filter_by(slug="particle-wa").first()
        exercise = build_exercise(grammar, [grammar])
        assert exercise["type"] == "pattern"
        assert exercise["prompt"] == grammar.example_sentence
        assert exercise["answer"] == grammar.pattern
        assert answer_for(grammar) == grammar.pattern


def test_adaptive_selection_prioritizes_weak_items(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        weak = LearningItem.query.filter_by(slug="hiragana-a").first()
        other = LearningItem.query.filter_by(slug="hiragana-i").first()
        db.session.add(UserProgress(user=user, learning_item=weak, status="weak", mastery_level=0, accuracy=0))
        db.session.add(UserProgress(user=user, learning_item=other, status="reviewing", mastery_level=4, accuracy=100))
        db.session.commit()
        assert select_adaptive_item(user, [other, weak]) == weak


def test_practice_page_renders_exercise_metadata(client, app):
    with app.app_context():
        seed()
    register(client)
    response = client.get("/practice/grammar")
    assert response.status_code == 200
    assert b"Type the grammar pattern." in response.data
    response = client.get("/practice/kana")
    assert response.status_code == 200
    assert b"Type the romaji reading." in response.data


def test_correct_review_records_daily_activity_and_streak(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, item.reading, item.reading, True)
        db.session.commit()
        activity = DailyActivity.query.filter_by(user_id=user.id).first()
        assert activity.xp_earned == 10
        assert activity.reviews_completed == 1
        assert activity.correct_reviews == 1
        assert user.streak == 1


def test_wrong_review_counts_without_xp(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, "x", item.reading, False)
        db.session.commit()
        activity = DailyActivity.query.filter_by(user_id=user.id).first()
        assert activity.xp_earned == 0
        assert activity.reviews_completed == 1
        assert activity.wrong_reviews == 1
        assert user.streak == 1


def test_srs_stage_changes_after_correct_answer(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, item.reading, item.reading, True)
        db.session.commit()
        progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
        assert progress.srs_stage == 1


def test_mistake_log_created_after_wrong_answer(app):
    with app.app_context():
        seed()
        user = User(username="aki", email="aki@example.com")
        user.set_password("secret1")
        db.session.add(user)
        item = LearningItem.query.filter_by(item_type="kana").first()
        apply_review(user, item, "kana", item.japanese, "x", item.reading, False)
        db.session.commit()
        assert MistakeLog.query.filter_by(user_id=user.id).count() == 1


def test_admin_rejects_non_admin(client):
    register(client, username="admin", email="admin@example.com")
    client.get("/logout")
    register(client, username="aki", email="aki@example.com")
    response = client.get("/admin/items")
    assert response.status_code == 403
