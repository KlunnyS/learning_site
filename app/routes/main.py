from collections import Counter, defaultdict
from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    DailyActivity,
    ExampleSentence,
    LearningItem,
    Lesson,
    LessonProgress,
    LessonQuizAttempt,
    ListeningClip,
    MistakeLog,
    ReadingPassage,
    ReviewLog,
    UserNote,
    UserProgress,
    WritingAttempt,
    utcnow,
)
from app.services.recommendation_service import recommend_next
from app.services.exercise_service import answer_for, build_exercise, check_answer, select_adaptive_item
from app.services.learning_path_service import build_path_state, lesson_is_passed
from app.services.level_service import level_readiness
from app.services.progress_service import record_activity
from app.services.srs_service import apply_review, get_or_create_progress, mark_known, mark_seen

main_bp = Blueprint("main", __name__)

SKILL_TYPES = ["kana", "kanji", "vocabulary", "grammar", "reading", "listening", "writing_prompt", "conjugation"]


def progress_for(items):
    if not current_user.is_authenticated:
        return {}
    progress = UserProgress.query.filter(
        UserProgress.user_id == current_user.id,
        UserProgress.learning_item_id.in_([item.id for item in items] or [0]),
    ).all()
    return {p.learning_item_id: p for p in progress}


def lesson_progress_for(lessons):
    if not current_user.is_authenticated:
        return {}
    progress = LessonProgress.query.filter(
        LessonProgress.user_id == current_user.id,
        LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or [0]),
    ).all()
    return {p.lesson_id: p for p in progress}


def get_or_create_lesson_progress(lesson):
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = LessonProgress(
            user=current_user,
            lesson=lesson,
            status="in_progress",
            items_seen=0,
            exercises_correct=0,
            exercises_attempted=0,
            started_at=utcnow(),
        )
        db.session.add(progress)
    progress.last_activity = utcnow()
    return progress


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    activity = DailyActivity.query.filter_by(user_id=current_user.id, activity_date=today).first()
    due = UserProgress.query.filter(
        UserProgress.user_id == current_user.id,
        UserProgress.next_review.isnot(None),
        UserProgress.next_review <= utcnow(),
    ).all()
    due_by_type = Counter(p.learning_item.item_type for p in due)
    skill_cards = []
    for skill in SKILL_TYPES:
        total = LearningItem.query.filter_by(item_type=skill).count()
        known = (
            UserProgress.query.join(LearningItem)
            .filter(UserProgress.user_id == current_user.id, LearningItem.item_type == skill, UserProgress.mastery_level >= 3)
            .count()
        )
        skill_cards.append({"name": skill.replace("_prompt", "").replace("_", " ").title(), "known": known, "total": total})
    mistakes = MistakeLog.query.filter_by(user_id=current_user.id, resolved=False).order_by(MistakeLog.created_at.desc()).limit(5).all()
    return render_template(
        "main/dashboard.html",
        xp_today=activity.xp_earned if activity else 0,
        reviews_completed=activity.reviews_completed if activity else 0,
        lessons_completed=activity.lessons_completed if activity else 0,
        daily_goal_percent=round(((activity.xp_earned if activity else 0) / current_user.daily_goal_xp) * 100) if current_user.daily_goal_xp else 0,
        due_by_type=due_by_type,
        skill_cards=skill_cards,
        mistakes=mistakes,
        recommendation=recommend_next(current_user),
        readiness=level_readiness(current_user),
    )


@main_bp.route("/learn")
@login_required
def learn():
    items = LearningItem.query.order_by(LearningItem.item_type, LearningItem.id).all()
    return render_template("main/learn.html", items=items, progress_map=progress_for(items))


@main_bp.route("/study-path")
@login_required
def study_path():
    return render_template("main/study_path.html", path_entries=build_path_state(current_user))


@main_bp.route("/lessons/<slug>", methods=["GET", "POST"])
@login_required
def lesson_unit(slug):
    lesson = Lesson.query.filter_by(slug=slug).first_or_404()
    previous_lesson = Lesson.query.filter(Lesson.sequence < lesson.sequence).order_by(Lesson.sequence.desc(), Lesson.id.desc()).first()
    locked = bool(previous_lesson and not lesson_is_passed(current_user, previous_lesson))
    links = lesson.items
    items = [link.learning_item for link in links]
    lesson_examples = (
        ExampleSentence.query.filter(ExampleSentence.learning_item_id.in_([item.id for item in items] or [0]))
        .order_by(ExampleSentence.difficulty, ExampleSentence.id)
        .limit(6)
        .all()
    )
    lesson_progress = get_or_create_lesson_progress(lesson)
    if request.method == "POST":
        if locked:
            flash("Complete the previous lesson quiz before starting this lesson.", "warning")
            return redirect(url_for("main.study_path"))
        action = request.form.get("action")
        if action == "start":
            lesson_progress.status = "in_progress"
            lesson_progress.started_at = lesson_progress.started_at or utcnow()
            flash("Lesson started.", "success")
        elif action == "complete":
            for item in items:
                mark_seen(current_user, item)
            lesson_progress.status = "completed"
            lesson_progress.items_seen = len(items)
            lesson_progress.completed_at = utcnow()
            record_activity(current_user, xp=lesson.xp_reward, lessons=1)
            flash(f"Lesson completed. +{lesson.xp_reward} XP", "success")
        db.session.commit()
        return redirect(url_for("main.lesson_unit", slug=lesson.slug))
    return render_template(
        "main/lesson_unit.html",
        lesson=lesson,
        links=links,
        examples=lesson_examples,
        progress=lesson_progress,
        item_progress=progress_for(items),
        locked=locked,
        previous_lesson=previous_lesson,
        quiz_attempts=LessonQuizAttempt.query.filter_by(user_id=current_user.id, lesson_id=lesson.id)
        .order_by(LessonQuizAttempt.created_at.desc())
        .limit(3)
        .all(),
    )


@main_bp.route("/lessons/<slug>/practice", methods=["GET", "POST"])
@login_required
def lesson_practice(slug):
    lesson = Lesson.query.filter_by(slug=slug).first_or_404()
    previous_lesson = Lesson.query.filter(Lesson.sequence < lesson.sequence).order_by(Lesson.sequence.desc(), Lesson.id.desc()).first()
    if previous_lesson and not lesson_is_passed(current_user, previous_lesson):
        flash("Complete the previous lesson quiz before practicing this lesson.", "warning")
        return redirect(url_for("main.study_path"))
    items = [link.learning_item for link in lesson.items]
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = answer_for(item)
        is_correct = check_answer(item, answer)
        apply_review(current_user, item, f"lesson:{lesson.slug}", request.form.get("prompt"), answer, correct, is_correct)
        progress = get_or_create_lesson_progress(lesson)
        progress.exercises_attempted += 1
        if is_correct:
            progress.exercises_correct += 1
        progress.status = "completed" if progress.items_seen >= len(items) and progress.accuracy >= 80 else "in_progress"
        db.session.commit()
        flash("Correct." if is_correct else f"Not quite. Correct: {correct}", "success" if is_correct else "error")
        return redirect(url_for("main.lesson_practice", slug=lesson.slug))

    exercise = build_exercise(select_adaptive_item(current_user, items), items)
    return render_template("main/practice.html", kind=f"{lesson.title} Lesson", exercise=exercise)


@main_bp.route("/lessons/<slug>/quiz", methods=["GET", "POST"])
@login_required
def lesson_quiz(slug):
    lesson = Lesson.query.filter_by(slug=slug).first_or_404()
    previous_lesson = Lesson.query.filter(Lesson.sequence < lesson.sequence).order_by(Lesson.sequence.desc(), Lesson.id.desc()).first()
    if previous_lesson and not lesson_is_passed(current_user, previous_lesson):
        flash("Complete the previous lesson quiz before taking this quiz.", "warning")
        return redirect(url_for("main.study_path"))
    items = [link.learning_item for link in lesson.items]
    quiz_items = items[:5]
    if request.method == "POST":
        correct_count = 0
        answered_items = []
        for item in quiz_items:
            answer = request.form.get(f"answer_{item.id}", "").strip()
            correct = answer_for(item)
            is_correct = check_answer(item, answer)
            if is_correct:
                correct_count += 1
            apply_review(current_user, item, f"quiz:{lesson.slug}", request.form.get(f"prompt_{item.id}"), answer, correct, is_correct)
            answered_items.append(item)
        question_count = len(answered_items)
        score = round((correct_count / question_count) * 100, 1) if question_count else 0.0
        passed = score >= 80
        attempt = LessonQuizAttempt(
            user=current_user,
            lesson=lesson,
            correct_count=correct_count,
            question_count=question_count,
            score_percent=score,
            passed=passed,
        )
        db.session.add(attempt)
        progress = get_or_create_lesson_progress(lesson)
        progress.exercises_attempted += question_count
        progress.exercises_correct += correct_count
        if passed:
            progress.status = "completed"
            progress.items_seen = max(progress.items_seen, len(items))
            progress.completed_at = progress.completed_at or utcnow()
        db.session.commit()
        flash(f"Quiz score: {score}%.", "success" if passed else "warning")
        return redirect(url_for("main.lesson_unit", slug=lesson.slug))
    exercises = [build_exercise(item, items) for item in quiz_items]
    return render_template("main/lesson_quiz.html", lesson=lesson, exercises=exercises)


@main_bp.route("/learn/<slug>", methods=["GET", "POST"])
@login_required
def lesson(slug):
    item = LearningItem.query.filter_by(slug=slug).first_or_404()
    if request.method == "POST":
        action = request.form.get("action")
        if action == "seen":
            mark_seen(current_user, item)
            flash("Marked as seen.", "success")
        elif action == "known":
            mark_known(current_user, item)
            flash("Marked as known.", "success")
        elif action == "review":
            progress = mark_seen(current_user, item)
            progress.status = "reviewing"
            flash("Added to reviews.", "success")
        db.session.commit()
        return redirect(url_for("main.lesson", slug=item.slug))
    progress = UserProgress.query.filter_by(user_id=current_user.id, learning_item_id=item.id).first()
    examples = ExampleSentence.query.filter_by(learning_item_id=item.id).order_by(ExampleSentence.difficulty, ExampleSentence.id).all()
    template = "main/grammar_detail.html" if item.item_type == "grammar" else "main/lesson.html"
    return render_template(template, item=item, progress=progress, examples=examples)


@main_bp.route("/kana")
@main_bp.route("/kana/<script>")
@login_required
def kana(script=None):
    q = LearningItem.query.filter_by(item_type="kana")
    if script in {"hiragana", "katakana"}:
        q = q.filter(LearningItem.tags.contains(script))
    items = q.order_by(LearningItem.id).all()
    status = request.args.get("status", "all")
    pmap = progress_for(items)
    if status != "all":
        items = [item for item in items if pmap.get(item.id, None) and pmap[item.id].status == status]
    return render_template("main/kana.html", items=items, progress_map=pmap, script=script or "all")


@main_bp.route("/grammar")
@login_required
def grammar():
    items = LearningItem.query.filter_by(item_type="grammar").order_by(LearningItem.id).all()
    groups = defaultdict(list)
    for item in items:
        tag = (item.tags or "Basics").split(",")[0].strip().title()
        groups[tag].append(item)
    return render_template("main/grammar.html", groups=groups, progress_map=progress_for(items))


@main_bp.route("/vocabulary")
@login_required
def vocabulary():
    items = LearningItem.query.filter_by(item_type="vocabulary")
    jlpt = request.args.get("jlpt")
    tag = request.args.get("tag")
    if jlpt:
        items = items.filter_by(jlpt_level=jlpt)
    if tag:
        items = items.filter(LearningItem.tags.contains(tag))
    items = items.order_by(LearningItem.id).all()
    return render_template("main/cards.html", title="Vocabulary", items=items, progress_map=progress_for(items), practice_url="/practice/vocabulary")


@main_bp.route("/kanji")
@login_required
def kanji():
    items = LearningItem.query.filter_by(item_type="kanji").order_by(LearningItem.id).all()
    return render_template("main/cards.html", title="Kanji", items=items, progress_map=progress_for(items), practice_url="/practice/kanji")


@main_bp.route("/practice/<kind>", methods=["GET", "POST"])
@login_required
def practice(kind):
    allowed = {"kana", "vocabulary", "kanji", "grammar", "conjugation"}
    if kind not in allowed:
        flash("Practice mode not found.", "error")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = answer_for(item)
        is_correct = check_answer(item, answer)
        apply_review(current_user, item, kind, request.form.get("prompt"), answer, correct, is_correct)
        db.session.commit()
        flash("Correct." if is_correct else f"Not quite. Correct: {correct}", "success" if is_correct else "error")
        return redirect(url_for("main.practice", kind=kind))
    items = LearningItem.query.filter_by(item_type=kind).all()
    exercise = build_exercise(select_adaptive_item(current_user, items), items)
    return render_template("main/practice.html", kind=kind, exercise=exercise)


@main_bp.route("/practice/listening", methods=["GET", "POST"])
@login_required
def practice_listening():
    """Practice listening by presenting a random clip and checking answer."""
    clips = ListeningClip.query.all()
    if not clips:
        flash("No listening clips available.", "info")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        clip_id = int(request.form.get("clip_id", 0))
        clip = db.session.get(ListeningClip, clip_id)
        answer = request.form.get("answer", "").strip()
        # Simple correctness: check if any token from transcript appears in answer
        correct_text = clip.transcript_japanese or ""
        is_correct = any(tok for tok in correct_text.split() if tok and tok in answer)
        apply_review(current_user, clip, "listening", request.form.get("prompt"), answer, correct_text, is_correct)
        flash("Answer submitted.", "success")
        return redirect(url_for("main.practice_listening"))
    # GET: select random clip
    import random
    clip = random.choice(clips)
    return render_template("main/listening_practice.html", clip=clip)


@main_bp.route("/reviews", methods=["GET", "POST"])
@login_required
def reviews():
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = answer_for(item)
        apply_review(current_user, item, "mixed", request.form.get("prompt"), answer, correct, check_answer(item, answer))
        db.session.commit()
        return redirect(url_for("main.reviews"))
    due = (
        UserProgress.query.filter(UserProgress.user_id == current_user.id, UserProgress.next_review.isnot(None), UserProgress.next_review <= utcnow())
        .order_by(UserProgress.next_review)
        .all()
    )
    exercise = build_exercise(due[0].learning_item, [progress.learning_item for progress in due]) if due else None
    return render_template("main/reviews.html", due=due, exercise=exercise)


def weak_items_for_current_user():
    weak_progress_items = [
        progress.learning_item
        for progress in UserProgress.query.filter_by(user_id=current_user.id, status="weak").all()
        if progress.learning_item
    ]
    mistake_items = [
        mistake.learning_item
        for mistake in MistakeLog.query.filter_by(user_id=current_user.id, resolved=False).all()
        if mistake.learning_item
    ]
    items_by_id = {item.id: item for item in weak_progress_items + mistake_items}
    return list(items_by_id.values())


def review_schedule_groups():
    now = utcnow()
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    tomorrow_end = today_end + timedelta(days=1)
    week_end = today_end + timedelta(days=7)
    rows = (
        UserProgress.query.filter(UserProgress.user_id == current_user.id, UserProgress.next_review.isnot(None))
        .order_by(UserProgress.next_review)
        .all()
    )
    groups = {"Due now": [], "Later today": [], "Tomorrow": [], "This week": [], "Later": []}
    for progress in rows:
        next_review = progress.next_review
        compare_now = now.replace(tzinfo=None) if next_review.tzinfo is None else now
        compare_today = today_end.replace(tzinfo=None) if next_review.tzinfo is None else today_end
        compare_tomorrow = tomorrow_end.replace(tzinfo=None) if next_review.tzinfo is None else tomorrow_end
        compare_week = week_end.replace(tzinfo=None) if next_review.tzinfo is None else week_end
        if next_review <= compare_now:
            groups["Due now"].append(progress)
        elif next_review <= compare_today:
            groups["Later today"].append(progress)
        elif next_review <= compare_tomorrow:
            groups["Tomorrow"].append(progress)
        elif next_review <= compare_week:
            groups["This week"].append(progress)
        else:
            groups["Later"].append(progress)
    return groups


@main_bp.route("/reviews/schedule")
@login_required
def review_schedule():
    groups = review_schedule_groups()
    return render_template("main/review_schedule.html", groups=groups, total=sum(len(items) for items in groups.values()))


@main_bp.route("/weak-practice", methods=["GET", "POST"])
@login_required
def weak_practice():
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = answer_for(item)
        is_correct = check_answer(item, answer)
        apply_review(current_user, item, "weak", request.form.get("prompt"), answer, correct, is_correct)
        if is_correct:
            MistakeLog.query.filter_by(user_id=current_user.id, learning_item_id=item.id, resolved=False).update({"resolved": True})
        db.session.commit()
        flash("Weak area reinforced." if is_correct else f"Still weak. Correct: {correct}", "success" if is_correct else "error")
        return redirect(url_for("main.weak_practice"))
    items = weak_items_for_current_user()
    exercise = build_exercise(select_adaptive_item(current_user, items), items)
    return render_template("main/practice.html", kind="Weak Areas", exercise=exercise)


@main_bp.route("/progress")
@login_required
def progress():
    reviews = ReviewLog.query.filter_by(user_id=current_user.id).all()
    activity = DailyActivity.query.filter_by(user_id=current_user.id).order_by(DailyActivity.activity_date.desc()).limit(14).all()
    quiz_attempts = LessonQuizAttempt.query.filter_by(user_id=current_user.id).order_by(LessonQuizAttempt.created_at.desc()).limit(8).all()
    total_correct = sum(1 for r in reviews if r.is_correct)
    total_wrong = len(reviews) - total_correct
    counts = {}
    for skill in SKILL_TYPES:
        counts[skill] = (
            UserProgress.query.join(LearningItem)
            .filter(UserProgress.user_id == current_user.id, LearningItem.item_type == skill, UserProgress.mastery_level >= 3)
            .count()
        )
    mistakes = MistakeLog.query.filter_by(user_id=current_user.id, resolved=False).order_by(MistakeLog.created_at.desc()).limit(10).all()
    accuracy = round((total_correct / len(reviews)) * 100, 1) if reviews else 0
    return render_template(
        "main/progress.html",
        reviews=reviews,
        total_correct=total_correct,
        total_wrong=total_wrong,
        counts=counts,
        mistakes=mistakes,
        accuracy=accuracy,
        activity=activity,
        quiz_attempts=quiz_attempts,
        readiness=level_readiness(current_user),
    )


@main_bp.route("/mastery")
@login_required
def mastery():
    progress_rows = (
        UserProgress.query.filter(UserProgress.user_id == current_user.id, UserProgress.mastery_level >= 3)
        .join(LearningItem)
        .order_by(LearningItem.item_type, LearningItem.title)
        .all()
    )
    grouped = defaultdict(lambda: {"learned": [], "mastered": []})
    for progress in progress_rows:
        item = progress.learning_item
        grouped[item.item_type]["learned"].append(progress)
        if progress.mastery_level >= 5 or progress.status == "mastered":
            grouped[item.item_type]["mastered"].append(progress)
    totals = {
        "learned": len(progress_rows),
        "mastered": sum(1 for progress in progress_rows if progress.mastery_level >= 5 or progress.status == "mastered"),
    }
    return render_template("main/mastery.html", grouped=dict(grouped), totals=totals)


@main_bp.route("/notebook", methods=["GET", "POST"])
@login_required
def notebook():
    if request.method == "POST":
        note = UserNote(user=current_user, title=request.form.get("title", "Untitled").strip(), body=request.form.get("body", "").strip())
        db.session.add(note)
        db.session.commit()
        flash("Note saved.", "success")
        return redirect(url_for("main.notebook"))
    return render_template(
        "main/notebook.html",
        unresolved=MistakeLog.query.filter_by(user_id=current_user.id, resolved=False).all(),
        resolved=MistakeLog.query.filter_by(user_id=current_user.id, resolved=True).all(),
        notes=UserNote.query.filter_by(user_id=current_user.id).order_by(UserNote.updated_at.desc()).all(),
    )


@main_bp.route("/notebook/mistakes/<int:mistake_id>/resolve", methods=["POST"])
@login_required
def resolve_mistake(mistake_id):
    mistake = MistakeLog.query.filter_by(id=mistake_id, user_id=current_user.id).first_or_404()
    mistake.resolved = True
    db.session.commit()
    return redirect(url_for("main.notebook"))


@main_bp.route("/notebook/notes/<int:note_id>/delete", methods=["POST"])
@login_required
def delete_note(note_id):
    note = UserNote.query.filter_by(id=note_id, user_id=current_user.id).first_or_404()
    db.session.delete(note)
    db.session.commit()
    return redirect(url_for("main.notebook"))


@main_bp.route("/writing", methods=["GET", "POST"])
@login_required
def writing():
    prompts = LearningItem.query.filter_by(item_type="writing_prompt").all()
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["prompt_id"]))
        text = request.form.get("user_text", "").strip()
        expected = (item.meaning or "").split("|")
        ok = bool(text) and any(token and token in text for token in expected)
        feedback = "Good attempt." if ok else f"Try including: {', '.join(expected)}. Model: {item.japanese}"
        db.session.add(WritingAttempt(user_id=current_user.id, prompt_id=item.id, user_text=text, feedback=feedback))
        record_activity(current_user, xp=5)
        if not ok:
            db.session.add(MistakeLog(user=current_user, learning_item=item, mistake_text=text or "(blank)", correct_answer=item.japanese, explanation=feedback))
        db.session.commit()
        flash(feedback, "success" if ok else "error")
        return redirect(url_for("main.writing"))
    attempts = WritingAttempt.query.filter_by(user_id=current_user.id).order_by(WritingAttempt.created_at.desc()).all()
    return render_template("main/writing.html", prompts=prompts, attempts=attempts)


@main_bp.route("/reading")
@login_required
def reading():
    passages = ReadingPassage.query.all()
    return render_template("main/reading.html", passages=passages)


@main_bp.route("/listening")
@login_required
def listening():
    clips = ListeningClip.query.all()
    return render_template("main/listening.html", clips=clips)


@main_bp.route("/conjugation")
@login_required
def conjugation():
    return redirect(url_for("main.practice", kind="conjugation"))


@main_bp.route("/onboarding")
@login_required
def onboarding():
    return redirect(url_for("main.onboarding_goal"))


@main_bp.route("/onboarding/goal", methods=["GET", "POST"])
@login_required
def onboarding_goal():
    if request.method == "POST":
        current_user.study_goal = request.form.get("study_goal")
        db.session.commit()
        return redirect(url_for("main.onboarding_level"))
    return render_template("main/onboarding_goal.html")


@main_bp.route("/onboarding/level", methods=["GET", "POST"])
@login_required
def onboarding_level():
    if request.method == "POST":
        current_user.starting_level = request.form.get("starting_level")
        db.session.commit()
        return redirect(url_for("main.onboarding_complete"))
    return render_template("main/onboarding_level.html")


@main_bp.route("/onboarding/complete")
@login_required
def onboarding_complete():
    current_user.onboarding_complete = True
    db.session.commit()
    flash("Onboarding complete.", "success")
    return redirect(url_for("main.dashboard"))
