from collections import Counter, defaultdict
from datetime import date
import random

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import (
    LearningItem,
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


def item_answer(item):
    if item.item_type == "kana":
        return item.reading or item.meaning or item.title
    if item.item_type in {"vocabulary", "kanji"}:
        return item.meaning or item.reading or item.japanese
    if item.item_type == "conjugation":
        return item.meaning
    return item.meaning or item.title


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("main/index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    today = date.today()
    today_reviews = ReviewLog.query.filter_by(user_id=current_user.id).all()
    today_reviews = [r for r in today_reviews if r.created_at.date() == today]
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
        xp_today=sum(10 for r in today_reviews if r.is_correct),
        reviews_completed=len(today_reviews),
        due_by_type=due_by_type,
        skill_cards=skill_cards,
        mistakes=mistakes,
        recommendation=recommend_next(current_user),
    )


@main_bp.route("/learn")
@login_required
def learn():
    items = LearningItem.query.order_by(LearningItem.item_type, LearningItem.id).all()
    return render_template("main/learn.html", items=items, progress_map=progress_for(items))


@main_bp.route("/study-path")
@login_required
def study_path():
    worlds = {
        "Kana Island": ["kana"],
        "Basic Sentences": ["grammar"],
        "Particles": ["grammar"],
        "Adjectives": ["grammar"],
        "Verbs": ["grammar", "conjugation"],
        "Kanji Forest": ["kanji"],
        "Reading Village": ["reading"],
        "Listening Harbor": ["listening"],
        "Writing Dojo": ["writing_prompt"],
    }
    all_items = LearningItem.query.order_by(LearningItem.id).all()
    progress_map = progress_for(all_items)
    grouped = {}
    for world, types in worlds.items():
        grouped[world] = [item for item in all_items if item.item_type in types][:8]
    return render_template("main/study_path.html", grouped=grouped, progress_map=progress_map)


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
    template = "main/grammar_detail.html" if item.item_type == "grammar" else "main/lesson.html"
    return render_template(template, item=item, progress=progress)


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
    allowed = {"kana", "vocabulary", "kanji", "conjugation"}
    if kind not in allowed:
        flash("Practice mode not found.", "error")
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = item_answer(item)
        is_correct = answer.lower() == (correct or "").lower()
        apply_review(current_user, item, kind, request.form.get("prompt"), answer, correct, is_correct)
        db.session.commit()
        flash("Correct." if is_correct else f"Not quite. Correct: {correct}", "success" if is_correct else "error")
        return redirect(url_for("main.practice", kind=kind))
    items = LearningItem.query.filter_by(item_type=kind).all()
    item = random.choice(items) if items else None
    choices = []
    if item and kind in {"kana", "vocabulary", "kanji"}:
        choices = [item_answer(x) for x in random.sample(items, min(4, len(items)))]
        if item_answer(item) not in choices:
            choices[0] = item_answer(item)
        random.shuffle(choices)
    return render_template("main/practice.html", kind=kind, item=item, answer=item_answer(item) if item else "", choices=choices)


@main_bp.route("/reviews", methods=["GET", "POST"])
@login_required
def reviews():
    if request.method == "POST":
        item = db.session.get(LearningItem, int(request.form["item_id"]))
        answer = request.form.get("answer", "").strip()
        correct = item_answer(item)
        apply_review(current_user, item, "mixed", request.form.get("prompt"), answer, correct, answer.lower() == (correct or "").lower())
        db.session.commit()
        return redirect(url_for("main.reviews"))
    due = (
        UserProgress.query.filter(UserProgress.user_id == current_user.id, UserProgress.next_review.isnot(None), UserProgress.next_review <= utcnow())
        .order_by(UserProgress.next_review)
        .all()
    )
    return render_template("main/reviews.html", due=due)


@main_bp.route("/progress")
@login_required
def progress():
    reviews = ReviewLog.query.filter_by(user_id=current_user.id).all()
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
    return render_template("main/progress.html", reviews=reviews, total_correct=total_correct, total_wrong=total_wrong, counts=counts, mistakes=mistakes, accuracy=accuracy)


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
        current_user.add_xp(5)
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
