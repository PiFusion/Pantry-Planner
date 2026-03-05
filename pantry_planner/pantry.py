from flask import Blueprint, render_template, request, redirect, url_for, session, g, jsonify
from .db import get_db

bp = Blueprint("pantry", __name__)


def _get_selected_ids():
    ids = session.get("selected_ingredient_ids")
    if not isinstance(ids, list):
        ids = []
    return set(int(x) for x in ids)


def _set_selected_ids(id_set):
    session["selected_ingredient_ids"] = sorted(list(id_set))


def _load_ingredients_and_selection(q: str):
    db = get_db()

    rows = db.execute(
        "SELECT id, name FROM ingredients WHERE hidden = 0 ORDER BY name"
    ).fetchall()
    all_ingredients = [{"id": r["id"], "name": r["name"]} for r in rows]

    if g.user:
        selected_rows = db.execute(
            "SELECT ingredient_id FROM pantry_items WHERE user_id = ?",
            (g.user["id"],),
        ).fetchall()
        selected_ids = {r["ingredient_id"] for r in selected_rows}
    else:
        selected_ids = _get_selected_ids()

    filtered_ingredients = all_ingredients
    if q:
        filtered_ingredients = [i for i in all_ingredients if q in i["name"].lower()]

    selected_ingredients = [i for i in all_ingredients if i["id"] in selected_ids]
    return filtered_ingredients, selected_ingredients, selected_ids


@bp.get("/ingredients")
def ingredients():
    q = request.args.get("q", "").strip().lower()
    filtered_ingredients, selected_ingredients, selected_ids = _load_ingredients_and_selection(q)

    return render_template(
        "pantry/ingredients.html",
        ingredients=filtered_ingredients,
        selected_ingredients=selected_ingredients,
        selected_ids=selected_ids,
        selected_count=len(selected_ids),
        q=q,
        last_action=request.args.get("last_action"),
        last_name=request.args.get("last_name"),
        last_ingredient_id=request.args.get("last_id", type=int),
    )


def _toggle_by_id(ingredient_id: int):
    db = get_db()
    ingredient = db.execute(
        "SELECT name FROM ingredients WHERE id = ?",
        (ingredient_id,),
    ).fetchone()
    ingredient_name = ingredient["name"] if ingredient else "ingredient"

    action = "added"
    if g.user:
        exists = db.execute(
            "SELECT 1 FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
            (g.user["id"], ingredient_id),
        ).fetchone()

        if exists:
            db.execute(
                "DELETE FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (g.user["id"], ingredient_id),
            )
            action = "removed"
        else:
            db.execute(
                "INSERT INTO pantry_items (user_id, ingredient_id) VALUES (?, ?)",
                (g.user["id"], ingredient_id),
            )
        db.commit()
    else:
        selected = _get_selected_ids()
        if ingredient_id in selected:
            selected.remove(ingredient_id)
            action = "removed"
        else:
            selected.add(ingredient_id)
        _set_selected_ids(selected)

    return action, ingredient_name


@bp.post("/ingredients/toggle")
def toggle_ingredient():
    ingredient_id = int(request.form["ingredient_id"])
    return_q = request.form.get("return_q", "")

    action, ingredient_name = _toggle_by_id(ingredient_id)

    return redirect(url_for(
        "pantry.ingredients",
        q=return_q,
        last_action=action,
        last_name=ingredient_name,
        last_id=ingredient_id,
    ))


@bp.post("/ingredients/toggle-async")
def toggle_ingredient_async():
    ingredient_id = int(request.form["ingredient_id"])
    q = request.form.get("return_q", "").strip().lower()

    action, ingredient_name = _toggle_by_id(ingredient_id)
    _, selected_ingredients, selected_ids = _load_ingredients_and_selection(q)

    return jsonify({
        "ok": True,
        "action": action,
        "ingredient_id": ingredient_id,
        "ingredient_name": ingredient_name,
        "selected_count": len(selected_ids),
        "selected_ingredients": selected_ingredients,
        "selected_ids": list(selected_ids),
    })


@bp.post("/ingredients/clear")
def clear_ingredients():
    return_q = request.form.get("return_q", "")
    db = get_db()

    if g.user:
        db.execute("DELETE FROM pantry_items WHERE user_id = ?", (g.user["id"],))
        db.commit()
    else:
        _set_selected_ids(set())

    return redirect(url_for("pantry.ingredients", q=return_q))


@bp.post("/ingredients/clear-async")
def clear_ingredients_async():
    db = get_db()

    if g.user:
        db.execute("DELETE FROM pantry_items WHERE user_id = ?", (g.user["id"],))
        db.commit()
    else:
        _set_selected_ids(set())

    return jsonify({"ok": True, "selected_count": 0, "selected_ingredients": [], "selected_ids": []})
