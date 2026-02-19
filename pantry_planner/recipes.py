from flask import Blueprint, render_template, g, session
from .db import get_db
from .integrations.mealdb import filter_meals_by_ingredient, lookup_meal

bp = Blueprint("recipes", __name__, url_prefix="/recipes")


def _selected_ingredient_names():
    db = get_db()

    if g.user:
        rows = db.execute(
            """
            SELECT i.name
            FROM pantry_items p
            JOIN ingredients i ON i.id = p.ingredient_id
            WHERE p.user_id = ?
            ORDER BY i.name
            """,
            (g.user["id"],),
        ).fetchall()
        return [r["name"] for r in rows]

    # Anonymous: map session IDs -> ingredient names
    ids = session.get("selected_ingredient_ids", [])
    if not ids:
        return []

    placeholders = ",".join("?" for _ in ids)
    rows = db.execute(
        f"SELECT name FROM ingredients WHERE id IN ({placeholders})",
        ids,
    ).fetchall()
    return [r["name"] for r in rows]


@bp.get("/search")
def search():
    selected_names = _selected_ingredient_names()

    if not selected_names:
        return render_template(
            "recipes/results.html",
            selected_names=[],
            results=[],
            message="No ingredients selected yet. Go select ingredients first.",
        )

    # Intersect MealDB results across ingredients (match ALL selected ingredients)
    first = filter_meals_by_ingredient(selected_names[0])
    base_map = {
        m["idMeal"]: {
            "idMeal": m["idMeal"],
            "strMeal": m.get("strMeal"),
            "strMealThumb": m.get("strMealThumb"),
        }
        for m in first
    }
    ids = set(base_map.keys())

    for ing in selected_names[1:]:
        meals = filter_meals_by_ingredient(ing)
        ids &= {m["idMeal"] for m in meals}
        if not ids:
            break

    results = [base_map[mid] for mid in ids if mid in base_map]
    results = sorted(results, key=lambda x: (x.get("strMeal") or ""))[:50]

    msg = None
    if not results:
        msg = "No recipes matched all selected ingredients."

    return render_template(
        "recipes/results.html",
        selected_names=selected_names,
        results=results,
        message=msg,
    )


@bp.get("/<meal_id>")
def detail(meal_id):
    meal = lookup_meal(meal_id)
    if not meal:
        return render_template("recipes/detail.html", meal=None, ingredients=[])

    pairs = []
    for i in range(1, 21):
        ing = (meal.get(f"strIngredient{i}") or "").strip()
        meas = (meal.get(f"strMeasure{i}") or "").strip()
        if ing:
            pairs.append({"ingredient": ing, "measure": meas})

    return render_template("recipes/detail.html", meal=meal, ingredients=pairs)
