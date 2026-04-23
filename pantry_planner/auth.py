from flask import Blueprint, render_template, request, redirect, url_for, session, g, flash
from werkzeug.security import generate_password_hash, check_password_hash
from .db import get_db

from sentry_sdk import set_user, add_breadcrumb

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")

    if user_id is None:
        g.user = None
        set_user(None)
    else:
        add_breadcrumb(
            category="auth",
            message=f"Loading user from session, user_id: {user_id}",
            level="info"
        )
        user = get_db().execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        g.user = user

        if user:
            set_user({
                "id": user["id"],
                "username": user["username"]
            })


@bp.get("/register")
@bp.post("/register")
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password are required.")
            return render_template("auth/register.html")

        add_breadcrumb(
            category="auth",
            message=f"Attempting to register new user: {username}",
            level="info"
        )

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
        except Exception:
            flash("Username is already taken.")
            return render_template("auth/register.html")

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@bp.get("/login")
@bp.post("/login")
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        add_breadcrumb(
            category="auth",
            message=f"Login attempt for user: {username}",
            level="info"
        )

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user is None or not check_password_hash(user["password_hash"], password):
            add_breadcrumb(
                category="auth",
                message=f"Failed login attempt for user: {username}",
                level="warning"
            )
            flash("Invalid username or password.")
            return render_template("auth/login.html")

        add_breadcrumb(
            category="auth",
            message=f"Clearing session and setting user_id: {user['id']}",
            level="info"
        )
        session.clear()
        session["user_id"] = user["id"]

        return redirect(url_for("pantry.ingredients"))

    return render_template("auth/login.html")


@bp.get("/logout")
def logout():
    add_breadcrumb(
        category="auth",
        message=f"Logging out user_id: {session.get('user_id')}",
        level="info"
    )
    session.clear()
    set_user(None)

    return redirect(url_for("pantry.ingredients"))