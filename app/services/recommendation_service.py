from app.models import LearningItem, MistakeLog, UserProgress, utcnow
from app.services.learning_path_service import next_path_step


def recommend_next(user):
    now = utcnow()
    due_count = UserProgress.query.filter(
        UserProgress.user_id == user.id,
        UserProgress.next_review.isnot(None),
        UserProgress.next_review <= now,
    ).count()
    if due_count:
        return {"title": "Review queue", "reason": f"You have {due_count} due reviews.", "url": "/reviews"}

    weak = (
        UserProgress.query.filter_by(user_id=user.id, status="weak")
        .join(LearningItem)
        .order_by(UserProgress.last_reviewed.desc().nullslast())
        .first()
    )
    if weak:
        return {
            "title": weak.learning_item.title,
            "reason": f"You often miss {weak.learning_item.title}.",
            "url": f"/learn/{weak.learning_item.slug}",
        }

    mistake = MistakeLog.query.filter_by(user_id=user.id, resolved=False).order_by(MistakeLog.created_at.desc()).first()
    if mistake:
        return {"title": "Notebook", "reason": "You have unresolved mistakes.", "url": "/notebook"}

    path_step = next_path_step(user)
    if path_step:
        return path_step

    seen_ids = [p.learning_item_id for p in UserProgress.query.filter_by(user_id=user.id).all()]
    unseen = LearningItem.query.filter(~LearningItem.id.in_(seen_ids)).order_by(LearningItem.id).first()
    if unseen:
        return {"title": unseen.title, "reason": "This is the next lesson in your study path.", "url": f"/learn/{unseen.slug}"}

    low = UserProgress.query.filter(UserProgress.user_id == user.id, UserProgress.mastery_level < 5).first()
    if low:
        return {"title": low.learning_item.title, "reason": "A low-mastery item is ready for practice.", "url": f"/learn/{low.learning_item.slug}"}

    return {"title": "Seed content", "reason": "No study content is available yet.", "url": "/learn"}
