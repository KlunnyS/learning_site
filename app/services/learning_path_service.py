from app.models import Lesson, LessonProgress, LessonQuizAttempt


def latest_quiz_attempt(user, lesson):
    return (
        LessonQuizAttempt.query.filter_by(user_id=user.id, lesson_id=lesson.id)
        .order_by(LessonQuizAttempt.created_at.desc())
        .first()
    )


def lesson_is_passed(user, lesson, progress=None):
    progress = progress or LessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first()
    quiz = latest_quiz_attempt(user, lesson)
    return bool((progress and progress.status == "completed") or (quiz and quiz.passed))


def build_path_state(user):
    lessons = Lesson.query.order_by(Lesson.sequence, Lesson.id).all()
    progress_rows = LessonProgress.query.filter(
        LessonProgress.user_id == user.id,
        LessonProgress.lesson_id.in_([lesson.id for lesson in lessons] or [0]),
    ).all()
    progress_by_lesson = {progress.lesson_id: progress for progress in progress_rows}
    states = []
    previous_passed = True
    first_available_seen = False
    for lesson in lessons:
        progress = progress_by_lesson.get(lesson.id)
        quiz = latest_quiz_attempt(user, lesson)
        passed = lesson_is_passed(user, lesson, progress)
        if not previous_passed:
            state = "locked"
            reason = "Complete the previous lesson quiz to unlock this lesson."
        elif passed:
            state = "completed"
            reason = "Lesson complete."
        elif quiz and not quiz.passed:
            state = "review"
            reason = "Review weak items and retake the quiz."
        elif progress and progress.status == "in_progress":
            state = "in_progress"
            reason = "Continue this lesson."
        elif not first_available_seen:
            state = "current"
            reason = "This is your next lesson."
            first_available_seen = True
        else:
            state = "upcoming"
            reason = "Available after your current lesson."
        states.append({"lesson": lesson, "progress": progress, "quiz": quiz, "state": state, "reason": reason})
        previous_passed = passed
    return states


def next_path_step(user):
    for entry in build_path_state(user):
        if entry["state"] in {"review", "in_progress", "current"}:
            lesson = entry["lesson"]
            return {
                "title": lesson.title,
                "reason": entry["reason"],
                "url": f"/lessons/{lesson.slug}",
            }
    return None
