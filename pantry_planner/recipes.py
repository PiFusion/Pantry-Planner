from flask import Blueprint, render_template, g, request, session

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
    raw_match_mode = request.args.get("match")
    match_mode = (raw_match_mode or "").strip().lower()
    if match_mode not in {"all", "any"}:
        # Backward-compatible alias from older links/docs.
        legacy_mode = request.args.get("mode", "").strip().lower()
        if legacy_mode in {"all", "strict"}:
            match_mode = "all"
        elif legacy_mode in {"any", "partial"}:
            match_mode = "any"
    if match_mode not in {"all", "any"}:
        match_mode = "any"

    sort_mode = request.args.get("sort", "match").strip().lower()
    if sort_mode not in {"match", "name"}:
        sort_mode = "match"

    min_match = request.args.get("min", type=int)

    if not selected_names:
        return render_template(
            "recipes/results.html",
            selected_names=[],
            results=[],
            message="No ingredients selected yet. Go select ingredients first.",
            match_mode=match_mode,
            sort_mode=sort_mode,
            min_match=1,
            effective_min=0,
        )

    result_map = {}
    for ingredient in selected_names:
        meals = filter_meals_by_ingredient(ingredient)
        for meal in meals:
            meal_id = meal.get("idMeal")
            if not meal_id:
                continue
            if meal_id not in result_map:
                result_map[meal_id] = {
                    "idMeal": meal_id,
                    "strMeal": meal.get("strMeal"),
                    "strMealThumb": meal.get("strMealThumb"),
                    "matched_count": 0,
                    "matched_ingredients": [],
                }

            if ingredient not in result_map[meal_id]["matched_ingredients"]:
                result_map[meal_id]["matched_ingredients"].append(ingredient)
                result_map[meal_id]["matched_count"] += 1

    if match_mode == "all":
        effective_min = len(selected_names)
    else:
        requested_min = min_match if min_match is not None else 1
        effective_min = max(1, min(requested_min, len(selected_names)))

    results = [meal for meal in result_map.values() if meal["matched_count"] >= effective_min]

    if sort_mode == "name":
        results = sorted(results, key=lambda x: (x.get("strMeal") or "", -(x.get("matched_count") or 0)))
    else:
        results = sorted(
            results,
            key=lambda x: (-(x.get("matched_count") or 0), x.get("strMeal") or ""),
        )

    results = results[:50]

    msg = None
    if not results and match_mode == "all":
        msg = "No recipes matched all selected ingredients. Try Partial Match mode."
    elif not results:
        msg = "No recipes matched the selected minimum threshold."
    elif match_mode == "any":
        msg = f"Showing recipes matching at least {effective_min} selected ingredient(s)."

    if match_mode == "all" and len(selected_names) == 1:
        strict_note = (
            "Strict and Partial behave the same when only 1 ingredient is selected. "
            "Select 2+ ingredients to see a difference."
        )
        msg = f"{msg} {strict_note}".strip() if msg else strict_note

    return render_template(
        "recipes/results.html",
        selected_names=selected_names,
        results=results,
        message=msg,
        match_mode=match_mode,
        sort_mode=sort_mode,
        min_match=min_match if min_match is not None else 1,
        effective_min=effective_min,
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
