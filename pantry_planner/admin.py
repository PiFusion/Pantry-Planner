from functools import wraps
from flask import Blueprint, render_template, redirect, request, url_for, flash, g

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

    user_q = request.args.get("user_q", "").strip()
    users = db.execute(
        """
        SELECT id, username, role, created_at
        FROM users
        WHERE username LIKE ?
        ORDER BY username
        LIMIT 100
        """,
        (f"%{user_q}%",),
    ).fetchall()

    manage_user_id = request.args.get("manage_user_id", type=int)
    manage_user = None
    selected_ingredients = []
    ingredient_q = request.args.get("ingredient_q", "").strip()
    candidate_ingredients = []

    if manage_user_id:
        manage_user = db.execute(
            "SELECT id, username, role FROM users WHERE id = ?",
            (manage_user_id,),
        ).fetchone()

        if manage_user:
            selected_ingredients = db.execute(
                """
                SELECT i.id, i.name
                FROM pantry_items p
                JOIN ingredients i ON i.id = p.ingredient_id
                WHERE p.user_id = ?
                ORDER BY i.name
                """,
                (manage_user_id,),
            ).fetchall()

            candidate_ingredients = db.execute(
                """
                SELECT i.id, i.name
                FROM ingredients i
                LEFT JOIN pantry_items p
                  ON p.ingredient_id = i.id
                 AND p.user_id = ?
                WHERE p.id IS NULL
                  AND i.hidden = 0
                  AND i.name LIKE ?
                ORDER BY i.name
                LIMIT 50
                """,
                (manage_user_id, f"%{ingredient_q}%"),
            ).fetchall()

    ingredient_admin_q = request.args.get("ingredient_admin_q", "").strip()
    show_all_ingredients = request.args.get("show_all_ingredients") == "1"
    ingredient_params = [f"%{ingredient_admin_q}%"]
    ingredient_query = """
        SELECT id, name, hidden, updated_at
        FROM ingredients
        WHERE name LIKE ?
        ORDER BY name
    """
    if not show_all_ingredients:
        ingredient_query += " LIMIT 100"
    ingredient_rows = db.execute(ingredient_query, ingredient_params).fetchall()
    total_ingredient_matches = db.execute(
        "SELECT COUNT(*) AS c FROM ingredients WHERE name LIKE ?",
        (f"%{ingredient_admin_q}%",),
    ).fetchone()["c"]

    return render_template(
        "admin/panel.html",
        last_sync=(last_sync["last_sync"] if last_sync else None),
        ingredient_count=(count["c"] if count else 0),
        users=users,
        user_q=user_q,
        manage_user=manage_user,
        selected_ingredients=selected_ingredients,
        ingredient_q=ingredient_q,
        candidate_ingredients=candidate_ingredients,
        ingredient_admin_q=ingredient_admin_q,
        show_all_ingredients=show_all_ingredients,
        total_ingredient_matches=total_ingredient_matches,
        ingredient_rows=ingredient_rows,
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


@bp.post("/users/delete/<int:user_id>")
@admin_required
def delete_user(user_id):
    if request.form.get("confirm_delete") != "yes":
        flash("Delete cancelled.")
        return redirect(request.referrer or url_for("admin.panel"))

    db = get_db()
    target = db.execute("SELECT id, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
    if target is None:
        flash("User not found.")
        return redirect(request.referrer or url_for("admin.panel"))

    if g.user["id"] == user_id:
        flash("You cannot delete your own admin account while logged in.")
        return redirect(request.referrer or url_for("admin.panel"))

    if target["role"] == "admin" and request.form.get("admin_confirm_username") != target["username"]:
        flash("To delete an admin, type the exact username in the confirmation prompt.")
        return redirect(request.referrer or url_for("admin.panel"))

    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()
    flash("User deleted.")
    return redirect(request.referrer or url_for("admin.panel"))


@bp.post("/users/<int:user_id>/ingredients/add")
@admin_required
def add_user_ingredient(user_id):
    ingredient_id = request.form.get("ingredient_id", type=int)
    if not ingredient_id:
        flash("Select an ingredient to add.")
        return redirect(request.referrer or url_for("admin.panel", manage_user_id=user_id))

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    ingredient = db.execute("SELECT id FROM ingredients WHERE id = ?", (ingredient_id,)).fetchone()
    if user is None or ingredient is None:
        flash("User or ingredient no longer exists.")
        return redirect(request.referrer or url_for("admin.panel", manage_user_id=user_id))

    db.execute(
        "INSERT OR IGNORE INTO pantry_items (user_id, ingredient_id) VALUES (?, ?)",
        (user_id, ingredient_id),
    )
    db.commit()
    flash("Ingredient added to user pantry.")
    return redirect(request.referrer or url_for("admin.panel", manage_user_id=user_id))


@bp.post("/users/<int:user_id>/ingredients/remove/<int:ingredient_id>")
@admin_required
def remove_user_ingredient(user_id, ingredient_id):
    db = get_db()
    db.execute(
        "DELETE FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
        (user_id, ingredient_id),
    )
    db.commit()
    flash("Ingredient removed from user pantry.")
    return redirect(request.referrer or url_for("admin.panel", manage_user_id=user_id))


@bp.post("/ingredients/toggle-hidden/<int:ingredient_id>")
@admin_required
def toggle_hidden_ingredient(ingredient_id):
    if request.form.get("confirm_blacklist") != "yes":
        flash("Blacklist update cancelled.")
        return redirect(request.referrer or url_for("admin.panel"))

    db = get_db()
    row = db.execute("SELECT id FROM ingredients WHERE id = ?", (ingredient_id,)).fetchone()
    if row is None:
        flash("Ingredient not found.")
        return redirect(request.referrer or url_for("admin.panel"))

    db.execute(
        """
        UPDATE ingredients
        SET hidden = CASE hidden WHEN 1 THEN 0 ELSE 1 END,
            updated_at = datetime('now')
        WHERE id = ?
        """,
        (ingredient_id,),
    )
    db.commit()
    flash("Ingredient visibility updated.")
    return redirect(request.referrer or url_for("admin.panel"))
