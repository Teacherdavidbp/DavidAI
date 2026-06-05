"""DavidAI — Safety MVP Flask application with PostgreSQL authentication."""

import os
import sys
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy.exc import IntegrityError

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from backend.extensions import db, login_manager  # noqa: E402
from database.config import SQLALCHEMY_DATABASE_URI  # noqa: E402
from database.models import User  # noqa: E402


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
        static_folder=os.path.join(BASE_DIR, "frontend", "static"),
    )

    app.config.update(
        SECRET_KEY=os.environ.get("DAVIDAI_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=SQLALCHEMY_DATABASE_URI,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        REMEMBER_COOKIE_DURATION=timedelta(days=30),
        REMEMBER_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(days=7),
    )

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please sign in to access this page."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    register_routes(app)
    return app


def register_routes(app: Flask) -> None:
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            full_name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not full_name or not email or not password:
                flash("All fields are required.", "error")
            elif len(password) < 8:
                flash("Password must be at least 8 characters.", "error")
            elif password != confirm_password:
                flash("Passwords do not match.", "error")
            elif db.session.scalar(db.select(User).filter_by(email=email)):
                flash("An account with that email already exists.", "error")
            else:
                user = User(full_name=full_name, email=email)
                user.set_password(password)
                db.session.add(user)
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash("An account with that email already exists.", "error")
                else:
                    login_user(user, remember=True)
                    flash("Account created. Welcome to DavidAI.", "success")
                    return redirect(url_for("home"))

        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("home"))

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            remember = request.form.get("remember") == "on"

            user = db.session.scalar(db.select(User).filter_by(email=email))

            if user is None or not user.check_password(password):
                flash("Invalid email or password.", "error")
            elif not user.is_active:
                flash("This account has been deactivated.", "error")
            else:
                login_user(user, remember=remember)
                flash(f"Welcome back, {user.display_name}.", "success")
                next_page = request.args.get("next")
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)
                return redirect(url_for("home"))

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "info")
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def home():
        return render_template("dashboard.html", page="home")

    @app.route("/chat")
    @login_required
    def chat():
        return render_template("chat.html", page="chat")

    @app.route("/safety")
    @login_required
    def safety():
        return render_template("safety.html", page="safety")

    @app.route("/profile")
    @login_required
    def profile():
        return render_template("profile.html", page="profile")


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
