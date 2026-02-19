from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, flash, g

from .db import get_db
from .integrations.mealdb import fetch_ingredients

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in.")
            return redirect(url_for("auth.login"))
        if g.user["role"] != "admin":
            flash("Admin access required.")
            return redirect(url_for("pantry.ingredients"))
        return view(*args, **kwargs)

    return wrapped


@bp.get("/")
@admin_required
def panel():
    db = get_db()
    last_sync = db.execute("SELECT MAX(updated_at) AS last_sync FROM ingredients").fetchone()
    count = db.execute("SELECT COUNT(*) AS c FROM ingredients").fetchone()
    return render_template(
        "admin/panel.html",
        last_sync=(last_sync["last_sync"] if last_sync else None),
        ingredient_count=(count["c"] if count else 0),
    )


@bp.post("/sync-ingredients")
@admin_required
def sync_ingredients():
    db = get_db()
    items = fetch_ingredients()

    for ing in items:
        name = ing["name"]
        mealdb_id = ing.get("mealdb_id")

        db.execute(
            """
            INSERT INTO ingredients (name, mealdb_id, updated_at)
            VALUES (?, ?, datetime('now'))
            ON CONFLICT(name) DO UPDATE SET
              mealdb_id = excluded.mealdb_id,
              updated_at = datetime('now')
            """,
            (name, mealdb_id),
        )

    db.commit()
    flash(f"Synced {len(items)} ingredients from MealDB.")
    return redirect(url_for("admin.panel"))
