from datetime import timedelta

from app.extensions import db
from app.models import MistakeLog, ReviewLog, UserProgress, utcnow
from app.services.progress_service import record_activity

STAGE_INTERVALS = {
    0: timedelta(minutes=10),
    1: timedelta(hours=4),
    2: timedelta(hours=8),
    3: timedelta(days=1),
    4: timedelta(days=3),
    5: timedelta(days=7),
    6: timedelta(days=14),
    7: timedelta(days=30),
}


def get_or_create_progress(user, item):
    progress = UserProgress.query.filter_by(user_id=user.id, learning_item_id=item.id).first()
    if not progress:
        progress = UserProgress(
            user=user,
            learning_item=item,
            status="unknown",
            mastery_level=0,
            accuracy=0.0,
            correct_count=0,
            wrong_count=0,
            srs_stage=0,
        )
        db.session.add(progress)
    return progress


def mark_seen(user, item):
    progress = get_or_create_progress(user, item)
    now = utcnow()
    progress.status = "seen"
    progress.mastery_level = max(progress.mastery_level, 1)
    progress.last_seen = now
    progress.next_review = now
    return progress


def mark_known(user, item):
    progress = get_or_create_progress(user, item)
    now = utcnow()
    progress.status = "known"
    progress.mastery_level = max(progress.mastery_level, 3)
    progress.last_seen = now
    progress.next_review = now + STAGE_INTERVALS[3]
    return progress


def apply_review(user, item, review_type, prompt, user_answer, correct_answer, is_correct):
    progress = get_or_create_progress(user, item)
    now = utcnow()
    progress.correct_count = progress.correct_count or 0
    progress.wrong_count = progress.wrong_count or 0
    progress.srs_stage = progress.srs_stage or 0
    progress.mastery_level = progress.mastery_level or 0
    if is_correct:
        progress.correct_count += 1
        progress.srs_stage = min(7, progress.srs_stage + 1)
        progress.mastery_level = min(5, max(progress.mastery_level, min(5, progress.srs_stage)))
        progress.status = "mastered" if progress.srs_stage >= 7 else "reviewing"
        record_activity(user, xp=10, reviews=1, correct_reviews=1)
    else:
        record_activity(user, reviews=1, wrong_reviews=1)
        progress.wrong_count += 1
        progress.srs_stage = max(0, progress.srs_stage - 1)
        progress.mastery_level = max(0, progress.mastery_level - 1)
        progress.status = "weak"
        progress.next_review = now + timedelta(minutes=15)
        db.session.add(
            MistakeLog(
                user=user,
                learning_item=item,
                mistake_text=user_answer or "(blank)",
                correct_answer=correct_answer,
                explanation=f"Review the answer for {item.title}.",
            )
        )
    if is_correct:
        progress.next_review = now + STAGE_INTERVALS[progress.srs_stage]
    progress.last_reviewed = now
    progress.recalculate_accuracy()
    db.session.add(
        ReviewLog(
            user=user,
            learning_item=item,
            review_type=review_type,
            prompt=prompt,
            user_answer=user_answer,
            correct_answer=correct_answer,
            is_correct=is_correct,
        )
    )
    return progress
