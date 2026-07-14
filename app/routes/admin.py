from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import ExampleSentence, LearningItem, Lesson, LessonItem

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


@admin_bp.route("/")
@admin_required
def index():
    return redirect(url_for("admin.items"))


@admin_bp.route("/lessons")
@admin_required
def lessons():
    return render_template("admin/lessons.html", lessons=Lesson.query.order_by(Lesson.sequence, Lesson.id).all())


@admin_bp.route("/lessons/new", methods=["GET", "POST"])
@admin_required
def new_lesson():
    lesson = Lesson()
    if request.method == "POST":
        db.session.add(lesson)
        save_lesson(lesson)
        db.session.commit()
        flash("Lesson created.", "success")
        return redirect(url_for("admin.lessons"))
    return render_template("admin/lesson_form.html", lesson=lesson, item_slugs="")


@admin_bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_lesson(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    if request.method == "POST":
        save_lesson(lesson)
        db.session.commit()
        flash("Lesson updated.", "success")
        return redirect(url_for("admin.lessons"))
    item_slugs = "\n".join(link.learning_item.slug for link in lesson.items)
    return render_template("admin/lesson_form.html", lesson=lesson, item_slugs=item_slugs)


@admin_bp.route("/lessons/<int:lesson_id>/delete", methods=["POST"])
@admin_required
def delete_lesson(lesson_id):
    lesson = db.session.get(Lesson, lesson_id) or abort(404)
    db.session.delete(lesson)
    db.session.commit()
    flash("Lesson deleted.", "success")
    return redirect(url_for("admin.lessons"))


@admin_bp.route("/items")
@admin_required
def items():
    q = LearningItem.query
    search = request.args.get("q", "").strip()
    item_type = request.args.get("type", "").strip()
    if search:
        q = q.filter(LearningItem.title.contains(search) | LearningItem.slug.contains(search))
    if item_type:
        q = q.filter_by(item_type=item_type)
    return render_template("admin/items.html", items=q.order_by(LearningItem.id.desc()).all(), search=search, item_type=item_type)


@admin_bp.route("/items/new", methods=["GET", "POST"])
@admin_required
def new_item():
    item = LearningItem()
    if request.method == "POST":
        save_item(item)
        db.session.add(item)
        db.session.commit()
        flash("Item created.", "success")
        return redirect(url_for("admin.items"))
    return render_template("admin/item_form.html", item=item)


@admin_bp.route("/items/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_item(item_id):
    item = db.session.get(LearningItem, item_id) or abort(404)
    if request.method == "POST":
        save_item(item)
        db.session.commit()
        flash("Item updated.", "success")
        return redirect(url_for("admin.items"))
    return render_template("admin/item_form.html", item=item)


@admin_bp.route("/items/<int:item_id>/delete", methods=["POST"])
@admin_required
def delete_item(item_id):
    item = db.session.get(LearningItem, item_id) or abort(404)
    db.session.delete(item)
    db.session.commit()
    flash("Item deleted.", "success")
    return redirect(url_for("admin.items"))


@admin_bp.route("/examples")
@admin_required
def examples():
    q = ExampleSentence.query.join(LearningItem)
    search = request.args.get("q", "").strip()
    item_type = request.args.get("type", "").strip()
    if search:
        q = q.filter(ExampleSentence.japanese.contains(search) | ExampleSentence.english.contains(search) | LearningItem.title.contains(search))
    if item_type:
        q = q.filter(LearningItem.item_type == item_type)
    return render_template(
        "admin/examples.html",
        examples=q.order_by(ExampleSentence.id.desc()).all(),
        search=search,
        item_type=item_type,
    )


@admin_bp.route("/examples/new", methods=["GET", "POST"])
@admin_required
def new_example():
    example = ExampleSentence()
    if request.method == "POST":
        save_example(example)
        db.session.add(example)
        db.session.commit()
        flash("Example created.", "success")
        return redirect(url_for("admin.examples"))
    return render_template("admin/example_form.html", example=example, items=LearningItem.query.order_by(LearningItem.item_type, LearningItem.title).all())


@admin_bp.route("/examples/<int:example_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_example(example_id):
    example = db.session.get(ExampleSentence, example_id) or abort(404)
    if request.method == "POST":
        save_example(example)
        db.session.commit()
        flash("Example updated.", "success")
        return redirect(url_for("admin.examples"))
    return render_template("admin/example_form.html", example=example, items=LearningItem.query.order_by(LearningItem.item_type, LearningItem.title).all())


@admin_bp.route("/examples/<int:example_id>/delete", methods=["POST"])
@admin_required
def delete_example(example_id):
    example = db.session.get(ExampleSentence, example_id) or abort(404)
    db.session.delete(example)
    db.session.commit()
    flash("Example deleted.", "success")
    return redirect(url_for("admin.examples"))


def save_item(item):
    for field in [
        "item_type",
        "slug",
        "title",
        "japanese",
        "reading",
        "meaning",
        "explanation",
        "pattern",
        "example_sentence",
        "jlpt_level",
        "source_name",
        "source_url",
        "tags",
    ]:
        setattr(item, field, request.form.get(field, "").strip() or None)
    item.difficulty = int(request.form.get("difficulty") or 1)


def save_example(example):
    example.learning_item_id = int(request.form.get("learning_item_id") or 0)
    for field in ["japanese", "reading", "english", "note", "source_name", "source_url"]:
        setattr(example, field, request.form.get(field, "").strip() or None)
    example.difficulty = int(request.form.get("difficulty") or 1)


def save_lesson(lesson):
    for field in ["slug", "title", "description", "level", "skill_focus"]:
        setattr(lesson, field, request.form.get(field, "").strip() or None)
    lesson.sequence = int(request.form.get("sequence") or 0)
    lesson.xp_reward = int(request.form.get("xp_reward") or 20)
    db.session.flush()
    LessonItem.query.filter_by(lesson_id=lesson.id).delete()
    raw_slugs = request.form.get("item_slugs", "")
    slugs = [slug.strip() for part in raw_slugs.splitlines() for slug in part.split(",") if slug.strip()]
    for position, slug in enumerate(slugs, start=1):
        item = LearningItem.query.filter_by(slug=slug).first()
        if item:
            db.session.add(LessonItem(lesson=lesson, learning_item=item, position=position))
