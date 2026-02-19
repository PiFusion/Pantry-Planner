from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, g, flash
from .db import get_db
from .integrations.mealdb import lookup_meal

bp = Blueprint("bookmarks", __name__, url_prefix="/bookmarks")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to use bookmarks.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@bp.get("/")
@login_required
def list_bookmarks():
    db = get_db()
    rows = db.execute(
        """
        SELECT mealdb_meal_id, meal_name, meal_thumb, created_at
        FROM bookmarks
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (g.user["id"],),
    ).fetchall()
    return render_template("bookmarks/list.html", bookmarks=rows)


@bp.post("/add/<meal_id>")
@login_required
def add(meal_id):
    db = get_db()
    meal = lookup_meal(meal_id)
    name = meal.get("strMeal") if meal else None
    thumb = meal.get("strMealThumb") if meal else None

    db.execute(
        """
        INSERT OR IGNORE INTO bookmarks (user_id, mealdb_meal_id, meal_name, meal_thumb)
        VALUES (?, ?, ?, ?)
        """,
        (g.user["id"], meal_id, name, thumb),
    )
    db.commit()
    return redirect(url_for("bookmarks.list_bookmarks"))


@bp.post("/remove/<meal_id>")
@login_required
def remove(meal_id):
    db = get_db()
    db.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND mealdb_meal_id = ?",
        (g.user["id"], meal_id),
    )
    db.commit()
    return redirect(url_for("bookmarks.list_bookmarks"))
