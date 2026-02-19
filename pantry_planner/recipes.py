from flask import Blueprint, render_template, g, session, request
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
    total = len(selected_names)

    if total == 0:
        return render_template(
            "recipes/results.html",
            selected_names=[],
            results=[],
            message="No ingredients selected yet. Go select ingredients first.",
            mode="partial",
            min_match=1,
            total_selected=0,
        )

    mode = request.args.get("mode", "partial").strip().lower()
    try:
        min_match = int(request.args.get("min", "2"))
    except ValueError:
        min_match = 2

    # Clamp min_match
    if min_match < 1:
        min_match = 1
    if min_match > total:
        min_match = total

    if mode == "all":
        min_match = total

    meal_counts = {}  # meal_id -> count of matched ingredients
    meal_info = {}    # meal_id -> basic info

    for ing in selected_names:
        meals = filter_meals_by_ingredient(ing) or []
        for m in meals:
            mid = m.get("idMeal")
            if not mid:
                continue
            meal_counts[mid] = meal_counts.get(mid, 0) + 1
            if mid not in meal_info:
                meal_info[mid] = {
                    "idMeal": mid,
                    "strMeal": m.get("strMeal"),
                    "strMealThumb": m.get("strMealThumb"),
                }

    results = []
    for mid, count in meal_counts.items():
        if count >= min_match:
            info = meal_info.get(mid, {"idMeal": mid, "strMeal": "", "strMealThumb": ""})
            info = dict(info)
            info["match_count"] = count
            info["match_percent"] = round((count / total) * 100)
            results.append(info)

    results.sort(key=lambda x: (-x["match_count"], (x.get("strMeal") or "")))
    results = results[:75]

    msg = None
    if not results:
        if mode == "all":
            msg = "No recipes matched ALL selected ingredients. Try partial match (e.g., at least 2)."
        else:
            msg = "No recipes matched your minimum. Try lowering the minimum match."

    return render_template(
        "recipes/results.html",
        selected_names=selected_names,
        results=results,
        message=msg,
        mode=mode,
        min_match=min_match,
        total_selected=total,
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