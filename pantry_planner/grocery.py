from functools import wraps
from datetime import datetime

from flask import Blueprint, flash, g, jsonify, redirect, render_template, request, url_for

from .db import get_db

bp = Blueprint("grocery", __name__, url_prefix="/grocery")

UNIT_ALIASES = {
    "pounds": "lb",
    "pound": "lb",
    "lbs": "lb",
    "ounces": "oz",
    "ounce": "oz",
    "grams": "g",
    "gram": "g",
    "kilograms": "kg",
    "kilogram": "kg",
    "tablespoons": "tbsp",
    "tablespoon": "tbsp",
    "teaspoons": "tsp",
    "teaspoon": "tsp",
    "cups": "cup",
    "bags": "bag",
    "counts": "ct",
}


def _parse_quantity(raw_quantity: str):
    text = (raw_quantity or "").strip()
    if not text:
        return None, None, None, None

    parts = text.split()
    try:
        amount = float(parts[0])
    except ValueError:
        return text, None, None, "unparsed"

    unit = " ".join(parts[1:]).lower().strip() if len(parts) > 1 else ""
    if unit in UNIT_ALIASES:
        unit = UNIT_ALIASES[unit]

    return text, amount, (unit or None), ("parsed" if unit else "parsed")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to manage your grocery list.")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


def _normalized_quantity(quantity: str, unit: str):
    qty = quantity.strip()
    unit_value = unit.strip()
    if qty and unit_value:
        return f"{qty} {unit_value}"
    return qty or None


def _insert_item_for_user(item_name: str, quantity: str | None, notes: str | None):
    db = get_db()
    raw_quantity, amount, unit, parse_status = _parse_quantity(quantity or "")
    db.execute(
        """
        INSERT INTO grocery_items (
          user_id, item_name, quantity, quantity_amount, quantity_unit, quantity_unit_normalized, quantity_parse_status, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            g.user["id"],
            item_name,
            raw_quantity,
            amount,
            unit,
            unit,
            parse_status,
            notes or None,
        ),
    )
    db.commit()


@bp.get("/")
@login_required
def list_items():
    ingredient_q = request.args.get("ingredient_q", "").strip()
    ingredient_q_lower = ingredient_q.lower()
    ingredient_rows = get_db().execute(
        """
        SELECT name
        FROM ingredients
        WHERE hidden = 0
        ORDER BY name ASC
        """
    ).fetchall()
    all_ingredients = [r["name"] for r in ingredient_rows]
    ingredient_suggestions = []
    if ingredient_q_lower:
        ingredient_suggestions = [n for n in all_ingredients if ingredient_q_lower in n.lower()][:8]

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
        ingredient_q=ingredient_q,
        ingredient_total=len(all_ingredients),
        ingredient_catalog=all_ingredients,
        ingredient_suggestions=ingredient_suggestions,
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

    _insert_item_for_user(item_name, quantity, notes)
    flash("Added to grocery list.")
    return redirect(url_for("grocery.list_items"))


@bp.post("/update/<int:item_id>")
@login_required
def update_item(item_id):
    quantity = request.form.get("quantity", "").strip()
    notes = request.form.get("notes", "").strip()

    db = get_db()
    raw_quantity, amount, unit, parse_status = _parse_quantity(quantity)
    db.execute(
        """
        UPDATE grocery_items
        SET quantity = ?,
            quantity_amount = ?,
            quantity_unit = ?,
            quantity_unit_normalized = ?,
            quantity_parse_status = ?,
            notes = ?
        WHERE id = ? AND user_id = ?
        """,
        (raw_quantity, amount, unit, unit, parse_status, notes or None, item_id, g.user["id"]),
    )
    db.commit()
    flash("Item details updated.")
    return redirect(url_for("grocery.list_items"))


@bp.post("/add-from-ingredients")
@login_required
def add_from_ingredients():
    item_name = request.form.get("item_name", "").strip()
    quantity = _normalized_quantity(
        request.form.get("quantity", ""),
        request.form.get("unit", ""),
    )
    notes = request.form.get("notes", "").strip()
    return_q = request.form.get("return_q", "").strip()

    if not item_name:
        flash("Ingredient name is required.")
        return redirect(url_for("pantry.ingredients", q=return_q))

    _insert_item_for_user(item_name, quantity, notes)
    flash(f"Added {item_name} to grocery list.")
    return redirect(url_for("pantry.ingredients", q=return_q))


@bp.post("/add-from-ingredients-async")
@login_required
def add_from_ingredients_async():
    item_name = request.form.get("item_name", "").strip()
    quantity = _normalized_quantity(
        request.form.get("quantity", ""),
        request.form.get("unit", ""),
    )
    notes = request.form.get("notes", "").strip()

    if not item_name:
        return jsonify({"ok": False, "error": "Ingredient name is required."}), 400

    _insert_item_for_user(item_name, quantity, notes)
    return jsonify({"ok": True, "item_name": item_name})


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
        printed_at=datetime.now().strftime("%b %d, %Y %I:%M %p").replace(" 0", " "),
        total_count=len(to_buy),
    )
