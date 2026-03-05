from functools import wraps
from flask import Blueprint, render_template, redirect, request, url_for, g, flash
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


def _safe_lookup(meal_id):
    try:
        return lookup_meal(meal_id)
    except Exception:
        return None


@bp.get("/")
@login_required
def list_bookmarks():
    q = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "newest").strip().lower()
    if sort not in {"newest", "name"}:
        sort = "newest"

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

    bookmarks = [dict(r) for r in rows]
    if q:
        bookmarks = [b for b in bookmarks if q in (b.get("meal_name") or "").lower()]

    if sort == "name":
        bookmarks = sorted(bookmarks, key=lambda b: (b.get("meal_name") or "").lower())

    selected_id = request.args.get("selected")
    if not selected_id and bookmarks:
        selected_id = bookmarks[0]["mealdb_meal_id"]

    selected = next((b for b in bookmarks if b["mealdb_meal_id"] == selected_id), None)
    selected_detail = _safe_lookup(selected_id) if selected_id else None

    return render_template(
        "bookmarks/list.html",
        bookmarks=bookmarks,
        selected_id=selected_id,
        selected=selected,
        selected_detail=selected_detail,
        q=q,
        sort=sort,
    )


@bp.post("/add/<meal_id>")
@login_required
def add(meal_id):
    db = get_db()
    meal = _safe_lookup(meal_id)
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
    return redirect(request.referrer or url_for("bookmarks.list_bookmarks"))


@bp.post("/remove/<meal_id>")
@login_required
def remove(meal_id):
    db = get_db()
    db.execute(
        "DELETE FROM bookmarks WHERE user_id = ? AND mealdb_meal_id = ?",
        (g.user["id"], meal_id),
    )
    db.commit()
    return redirect(request.referrer or url_for("bookmarks.list_bookmarks"))


@bp.post("/add-to-grocery/<meal_id>")
@login_required
def add_to_grocery(meal_id):
    meal = _safe_lookup(meal_id)
    if not meal:
        flash("Could not load recipe ingredients right now.")
        return redirect(url_for("bookmarks.list_bookmarks", selected=meal_id))

    db = get_db()
    added = 0
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        measure = (meal.get(f"strMeasure{i}") or "").strip()
        if not name:
            continue

        db.execute(
            """
            INSERT INTO grocery_items (user_id, item_name, quantity, notes)
            VALUES (?, ?, ?, ?)
            """,
            (g.user["id"], name, measure or None, f"From {meal.get('strMeal', 'bookmark')}"),
        )
        added += 1

    db.commit()
    flash(f"Added {added} ingredient(s) to grocery list.")
    return redirect(url_for("bookmarks.list_bookmarks", selected=meal_id))
