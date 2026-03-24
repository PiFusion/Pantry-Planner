from datetime import date, timedelta

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from .db import get_db
from .bookmarks import login_required
from .integrations.mealdb import lookup_meal

bp = Blueprint("planner", __name__, url_prefix="/planner")

DAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
SLOTS = ["lunch", "dinner"]
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


def _week_start_from_query() -> date:
    raw = (request.args.get("week_start") or "").strip()
    if raw:
        try:
            parsed = date.fromisoformat(raw)
            return parsed - timedelta(days=parsed.weekday())
        except ValueError:
            pass

    today = date.today()
    return today - timedelta(days=today.weekday())


def _ensure_week_plan(week_start: date) -> int:
    db = get_db()
    row = db.execute(
        "SELECT id FROM meal_plans WHERE user_id = ? AND week_start = ?",
        (g.user["id"], week_start.isoformat()),
    ).fetchone()
    if row:
        return row["id"]

    cursor = db.execute(
        "INSERT INTO meal_plans (user_id, week_start) VALUES (?, ?)",
        (g.user["id"], week_start.isoformat()),
    )
    db.commit()
    return cursor.lastrowid


def _parse_quantity(raw_quantity: str):
    text = (raw_quantity or "").strip()
    if not text:
        return {"raw": None, "amount": None, "unit": None}

    parts = text.split()
    first = parts[0]
    try:
        amount = float(first)
    except ValueError:
        return {"raw": text, "amount": None, "unit": None}

    unit = " ".join(parts[1:]).lower().strip() if len(parts) > 1 else ""
    if unit in UNIT_ALIASES:
        unit = UNIT_ALIASES[unit]

    return {
        "raw": text,
        "amount": amount,
        "unit": unit or None,
    }


def _grocery_key(name: str, parsed: dict):
    ingredient_name = (name or "").strip().lower()
    if parsed["amount"] is not None and parsed["unit"]:
        return ingredient_name, parsed["unit"]
    return ingredient_name, None


@bp.get("/")
@login_required
def week_view():
    week_start = _week_start_from_query()
    plan_id = _ensure_week_plan(week_start)
    db = get_db()

    entries = db.execute(
        """
        SELECT id, day_of_week, meal_slot, mealdb_meal_id, meal_name, meal_thumb
        FROM meal_plan_entries
        WHERE plan_id = ?
        ORDER BY day_of_week, meal_slot
        """,
        (plan_id,),
    ).fetchall()

    entry_map = {(e["day_of_week"], e["meal_slot"]): dict(e) for e in entries}

    bookmarks = db.execute(
        """
        SELECT mealdb_meal_id, meal_name, meal_thumb
        FROM bookmarks
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 60
        """,
        (g.user["id"],),
    ).fetchall()

    week_days = []
    for idx, label in enumerate(DAY_LABELS):
        week_days.append(
            {
                "index": idx,
                "label": label,
                "date": (week_start + timedelta(days=idx)).isoformat(),
                "lunch": entry_map.get((idx, "lunch")),
                "dinner": entry_map.get((idx, "dinner")),
            }
        )

    return render_template(
        "planner/week.html",
        week_start=week_start.isoformat(),
        prev_week=(week_start - timedelta(days=7)).isoformat(),
        next_week=(week_start + timedelta(days=7)).isoformat(),
        week_days=week_days,
        bookmarks=bookmarks,
    )


@bp.post("/entry")
@login_required
def add_entry():
    week_start = _week_start_from_query()
    plan_id = _ensure_week_plan(week_start)

    day_of_week = request.form.get("day_of_week", type=int)
    meal_slot = (request.form.get("meal_slot") or "").strip().lower()
    mealdb_meal_id = (request.form.get("mealdb_meal_id") or "").strip()
    meal_name = (request.form.get("meal_name") or "").strip() or "Planned meal"
    meal_thumb = (request.form.get("meal_thumb") or "").strip() or None

    if day_of_week is None or day_of_week < 0 or day_of_week > 6 or meal_slot not in SLOTS or not mealdb_meal_id:
        flash("Please choose a valid day, slot, and meal.")
        return redirect(url_for("planner.week_view", week_start=week_start.isoformat()))

    db = get_db()
    db.execute(
        """
        INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name, meal_thumb)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(plan_id, day_of_week, meal_slot) DO UPDATE SET
          mealdb_meal_id = excluded.mealdb_meal_id,
          meal_name = excluded.meal_name,
          meal_thumb = excluded.meal_thumb
        """,
        (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name, meal_thumb),
    )
    db.commit()
    flash(f"Added {meal_name} to plan.")
    return redirect(url_for("planner.week_view", week_start=week_start.isoformat()))


@bp.post("/entry/<int:entry_id>/delete")
@login_required
def delete_entry(entry_id):
    week_start = _week_start_from_query()
    db = get_db()
    db.execute(
        """
        DELETE FROM meal_plan_entries
        WHERE id = ?
          AND plan_id IN (SELECT id FROM meal_plans WHERE user_id = ?)
        """,
        (entry_id, g.user["id"]),
    )
    db.commit()
    flash("Plan entry removed.")
    return redirect(url_for("planner.week_view", week_start=week_start.isoformat()))


@bp.post("/generate-grocery")
@login_required
def generate_grocery():
    week_start = _week_start_from_query()
    selected_days = request.form.getlist("day_of_week")
    selected_set = {int(d) for d in selected_days if str(d).isdigit()}
    include_checked = request.form.get("include_checked") == "yes"

    db = get_db()
    plan = db.execute(
        "SELECT id FROM meal_plans WHERE user_id = ? AND week_start = ?",
        (g.user["id"], week_start.isoformat()),
    ).fetchone()
    if not plan:
        flash("No meal plan exists for this week yet.")
        return redirect(url_for("planner.week_view", week_start=week_start.isoformat()))

    entries = db.execute(
        """
        SELECT day_of_week, meal_name, mealdb_meal_id
        FROM meal_plan_entries
        WHERE plan_id = ?
        ORDER BY day_of_week, meal_slot
        """,
        (plan["id"],),
    ).fetchall()

    if selected_set:
        entries = [e for e in entries if e["day_of_week"] in selected_set]

    aggregate = {}
    for entry in entries:
        meal = lookup_meal(entry["mealdb_meal_id"])
        if not meal:
            continue

        for i in range(1, 21):
            ing_name = (meal.get(f"strIngredient{i}") or "").strip()
            measure = (meal.get(f"strMeasure{i}") or "").strip()
            if not ing_name:
                continue

            parsed = _parse_quantity(measure)
            key = _grocery_key(ing_name, parsed)
            note = f"From plan: {DAY_LABELS[entry['day_of_week']]} {entry['meal_name']}"

            if key not in aggregate:
                aggregate[key] = {
                    "item_name": ing_name,
                    "amount": parsed["amount"],
                    "unit": parsed["unit"],
                    "raw": parsed["raw"],
                    "notes": [note],
                }
            else:
                if parsed["amount"] is not None and aggregate[key]["amount"] is not None and parsed["unit"] == aggregate[key]["unit"]:
                    aggregate[key]["amount"] += parsed["amount"]
                elif parsed["raw"]:
                    existing_raw = aggregate[key]["raw"] or ""
                    aggregate[key]["raw"] = ", ".join(x for x in [existing_raw, parsed["raw"]] if x)
                aggregate[key]["notes"].append(note)

    added = 0
    for item in aggregate.values():
        quantity = item["raw"]
        if item["amount"] is not None and item["unit"]:
            amount = int(item["amount"]) if float(item["amount"]).is_integer() else round(item["amount"], 2)
            quantity = f"{amount} {item['unit']}"

        notes = " · ".join(dict.fromkeys(item["notes"]))[:280]
        db.execute(
            """
            INSERT INTO grocery_items (
              user_id, item_name, quantity, notes,
              quantity_amount, quantity_unit, quantity_unit_normalized, quantity_parse_status, is_checked
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                g.user["id"],
                item["item_name"],
                quantity,
                notes,
                item["amount"],
                item["unit"],
                item["unit"],
                "parsed" if item["amount"] is not None else "unparsed",
                1 if include_checked else 0,
            ),
        )
        added += 1

    db.commit()
    flash(f"Generated {added} grocery item(s) from meal plan.")
    return redirect(url_for("grocery.list_items"))
