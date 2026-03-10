from functools import wraps
from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db

bp = Blueprint("grocery", __name__, url_prefix="/grocery")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to manage your grocery list.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@bp.get("/")
@login_required
def list_items():
    rows = get_db().execute(
        """
        SELECT id, item_name, quantity, notes, is_checked, created_at
        FROM grocery_items
        WHERE user_id = ?
        ORDER BY is_checked ASC, created_at DESC
        """,
        (g.user["id"],),
    ).fetchall()

    to_buy = [r for r in rows if not r["is_checked"]]
    checked = [r for r in rows if r["is_checked"]]

    return render_template(
        "grocery/list.html",
        items=rows,
        to_buy=to_buy,
        checked=checked,
        total_count=len(rows),
        checked_count=len(checked),
    )


@bp.post("/add")
@login_required
def add_item():
    item_name = request.form.get("item_name", "").strip()
    quantity = request.form.get("quantity", "").strip()
    notes = request.form.get("notes", "").strip()

    if not item_name:
        flash("Item name is required.")
        return redirect(url_for("grocery.list_items"))

    db = get_db()
    db.execute(
        """
        INSERT INTO grocery_items (user_id, item_name, quantity, notes)
        VALUES (?, ?, ?, ?)
        """,
        (g.user["id"], item_name, quantity or None, notes or None),
    )
    db.commit()
    flash("Added to grocery list.")
    return redirect(url_for("grocery.list_items"))


@bp.post("/add-from-ingredients")
@login_required
def add_from_ingredients():
    item_name = request.form.get("item_name", "").strip()
    quantity = request.form.get("quantity", "").strip()
    notes = request.form.get("notes", "").strip()
    return_q = request.form.get("return_q", "").strip()

    if not item_name:
        flash("Ingredient name is required.")
        return redirect(url_for("pantry.ingredients", q=return_q))

    db = get_db()
    db.execute(
        """
        INSERT INTO grocery_items (user_id, item_name, quantity, notes)
        VALUES (?, ?, ?, ?)
        """,
        (g.user["id"], item_name, quantity or None, notes or None),
    )
    db.commit()
    flash(f"Added {item_name} to grocery list.")
    return redirect(url_for("pantry.ingredients", q=return_q))


@bp.post("/toggle/<int:item_id>")
@login_required
def toggle_item(item_id):
    db = get_db()
    row = db.execute(
        "SELECT is_checked FROM grocery_items WHERE id = ? AND user_id = ?",
        (item_id, g.user["id"]),
    ).fetchone()
    if row:
        db.execute(
            "UPDATE grocery_items SET is_checked = ? WHERE id = ? AND user_id = ?",
            (0 if row["is_checked"] else 1, item_id, g.user["id"]),
        )
        db.commit()
    return redirect(url_for("grocery.list_items"))


@bp.post("/delete/<int:item_id>")
@login_required
def delete_item(item_id):
    db = get_db()
    db.execute(
        "DELETE FROM grocery_items WHERE id = ? AND user_id = ?",
        (item_id, g.user["id"]),
    )
    db.commit()
    flash("Item deleted.")
    return redirect(url_for("grocery.list_items"))


@bp.post("/clear")
@login_required
def clear_all():
    db = get_db()
    db.execute("DELETE FROM grocery_items WHERE user_id = ?", (g.user["id"],))
    db.commit()
    flash("Grocery list cleared.")
    return redirect(url_for("grocery.list_items"))


@bp.post("/clear-checked")
@login_required
def clear_checked():
    db = get_db()
    db.execute(
        "DELETE FROM grocery_items WHERE user_id = ? AND is_checked = 1",
        (g.user["id"],),
    )
    db.commit()
    flash("Checked items removed.")
    return redirect(url_for("grocery.list_items"))


@bp.get("/print")
@login_required
def print_view():
    rows = get_db().execute(
        """
        SELECT item_name, quantity, notes, is_checked
        FROM grocery_items
        WHERE user_id = ?
        ORDER BY is_checked ASC, created_at DESC
        """,
        (g.user["id"],),
    ).fetchall()

    to_buy = [r for r in rows if not r["is_checked"]]

    return render_template(
        "grocery/print.html",
        items=to_buy,
        printed_at=datetime.now(),
        total_count=len(to_buy),
    )
