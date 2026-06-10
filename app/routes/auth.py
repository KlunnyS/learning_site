from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not username or not email or len(password) < 6:
            flash("Use a username, email, and password of at least 6 characters.", "error")
        elif User.query.filter((User.username == username) | (User.email == email)).first():
            flash("That username or email is already registered.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(password)
            user.is_admin = User.query.count() == 0
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to NihongoPath.", "success")
            return redirect(url_for("main.onboarding_goal"))
    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in.", "success")
            if not user.onboarding_complete:
                return redirect(url_for("main.onboarding_goal"))
            return redirect(request.args.get("next") or url_for("main.dashboard"))
        flash("Invalid login.", "error")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "success")
    return redirect(url_for("main.index"))
