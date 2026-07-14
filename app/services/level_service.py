from app.models import LearningItem, Lesson, LessonProgress, LessonQuizAttempt, MistakeLog, UserProgress

CORE_SKILLS = ["kana", "kanji", "vocabulary", "grammar", "conjugation", "reading", "listening", "writing_prompt"]


def pct(part, total):
    return round((part / total) * 100, 1) if total else 0.0


def level_readiness(user):
    skill_rows = []
    learned_total = 0
    possible_total = 0
    for skill in CORE_SKILLS:
        total = LearningItem.query.filter_by(item_type=skill).count()
        learned = (
            UserProgress.query.join(LearningItem)
            .filter(UserProgress.user_id == user.id, LearningItem.item_type == skill, UserProgress.mastery_level >= 3)
            .count()
        )
        mastered = (
            UserProgress.query.join(LearningItem)
            .filter(UserProgress.user_id == user.id, LearningItem.item_type == skill, UserProgress.mastery_level >= 5)
            .count()
        )
        learned_total += learned
        possible_total += total
        skill_rows.append(
            {
                "name": skill.replace("_prompt", "").replace("_", " ").title(),
                "item_type": skill,
                "learned": learned,
                "mastered": mastered,
                "total": total,
                "percent": pct(learned, total),
            }
        )

    lesson_total = Lesson.query.count()
    lessons_complete = LessonProgress.query.filter_by(user_id=user.id, status="completed").count()
    quiz_attempts = LessonQuizAttempt.query.filter_by(user_id=user.id).all()
    latest_by_lesson = {}
    for attempt in quiz_attempts:
        latest_by_lesson[attempt.lesson_id] = attempt
    passed_quizzes = sum(1 for attempt in latest_by_lesson.values() if attempt.passed)
    quiz_average = pct(sum(attempt.score_percent for attempt in latest_by_lesson.values()), len(latest_by_lesson))
    weak_count = MistakeLog.query.filter_by(user_id=user.id, resolved=False).count() + UserProgress.query.filter_by(user_id=user.id, status="weak").count()

    content_score = pct(learned_total, possible_total)
    lesson_score = pct(lessons_complete, lesson_total)
    quiz_score = pct(passed_quizzes, lesson_total)
    readiness = round((content_score * 0.45) + (lesson_score * 0.3) + (quiz_score * 0.25), 1)

    if readiness >= 90 and weak_count == 0:
        label = "N5 ready"
    elif readiness >= 65:
        label = "N5 building"
    elif readiness >= 30:
        label = "N5 foundations"
    else:
        label = "Starting N5"

    return {
        "label": label,
        "readiness": readiness,
        "content_score": content_score,
        "lesson_score": lesson_score,
        "quiz_score": quiz_score,
        "quiz_average": round(quiz_average, 1),
        "lessons_complete": lessons_complete,
        "lesson_total": lesson_total,
        "passed_quizzes": passed_quizzes,
        "weak_count": weak_count,
        "skills": skill_rows,
    }
