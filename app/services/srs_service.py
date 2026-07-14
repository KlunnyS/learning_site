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


def adjust_stage(progress, quality: int) -> None:
    """Adjust SRS stage based on review quality (0-5).
    Implements a simplified SM-2 algorithm:
    - quality >= 4: increase stage (up to max)
    - quality == 3: repeat same stage
    - quality <= 2: decrease stage (minimum 0)
    """
    if quality >= 4:
        progress.srs_stage = min(7, progress.srs_stage + 1)
    elif quality == 3:
        # keep same stage
        pass
    else:
        progress.srs_stage = max(0, progress.srs_stage - 1)
    # Update mastery level based on stage
    progress.mastery_level = min(5, max(progress.mastery_level, progress.srs_stage))


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


def apply_review(user, item, review_type, prompt, user_answer, correct_answer, is_correct, quality: int = 5):
    """Apply a review to a learning item.
    Added `quality` parameter (0‑5) for finer SRS control.
    """
    progress = get_or_create_progress(user, item)
    now = utcnow()
    progress.correct_count = progress.correct_count or 0
    progress.wrong_count = progress.wrong_count or 0
    progress.srs_stage = progress.srs_stage or 0
    progress.mastery_level = progress.mastery_level or 0

    # Update counters based on correctness
    if is_correct:
        progress.correct_count += 1
    else:
        progress.wrong_count += 1
        progress.next_review = now + timedelta(minutes=15)

    # Adjust stage based on quality using helper
    adjust_stage(progress, quality)

    # Determine status
    progress.status = (
        "mastered" if progress.srs_stage >= 7 else "reviewing" if is_correct else "weak"
    )

    # Record activity XP
    if is_correct:
        record_activity(user, xp=10, reviews=1, correct_reviews=1)
    else:
        record_activity(user, reviews=1, wrong_reviews=1)
        db.session.add(
            MistakeLog(
                user=user,
                learning_item=item,
                mistake_text=user_answer or "(blank)",
                correct_answer=correct_answer,
                explanation=f"Review the answer for {item.title}.",
            )
        )

    # Schedule next review based on updated stage
    if is_correct:
        progress.next_review = now + STAGE_INTERVALS.get(progress.srs_stage, timedelta(days=30))

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
