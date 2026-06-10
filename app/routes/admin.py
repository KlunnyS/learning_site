from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import LearningItem

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
