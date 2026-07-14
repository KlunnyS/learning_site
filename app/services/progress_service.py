from datetime import timedelta

from app.extensions import db
from app.models import DailyActivity, utcnow


def record_activity(user, xp=0, reviews=0, lessons=0, correct_reviews=0, wrong_reviews=0):
    now = utcnow()
    today = now.date()
    activity = DailyActivity.query.filter_by(user_id=user.id, activity_date=today).first()
    is_first_activity_today = activity is None
    if not activity:
        activity = DailyActivity(user=user, activity_date=today)
        db.session.add(activity)

    activity.xp_earned = (activity.xp_earned or 0) + xp
    activity.reviews_completed = (activity.reviews_completed or 0) + reviews
    activity.lessons_completed = (activity.lessons_completed or 0) + lessons
    activity.correct_reviews = (activity.correct_reviews or 0) + correct_reviews
    activity.wrong_reviews = (activity.wrong_reviews or 0) + wrong_reviews
    activity.last_activity_at = now

    if xp:
        user.add_xp(xp)
    if is_first_activity_today:
        yesterday = today - timedelta(days=1)
        had_yesterday = DailyActivity.query.filter_by(user_id=user.id, activity_date=yesterday).first() is not None
        user.streak = (user.streak or 0) + 1 if had_yesterday else 1
    return activity
