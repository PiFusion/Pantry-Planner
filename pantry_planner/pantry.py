from flask import Blueprint, render_template, request, redirect, url_for, session, g
from .db import get_db

bp = Blueprint("pantry", __name__)


def _get_selected_ids():
    ids = session.get("selected_ingredient_ids")
    if not isinstance(ids, list):
        ids = []
    return set(int(x) for x in ids)


def _set_selected_ids(id_set):
    session["selected_ingredient_ids"] = sorted(list(id_set))


@bp.get("/ingredients")
def ingredients():
    q = request.args.get("q", "").strip().lower()
    db = get_db()

    rows = db.execute(
        "SELECT id, name FROM ingredients WHERE hidden = 0 ORDER BY name"
    ).fetchall()

    ingredients = [{"id": r["id"], "name": r["name"]} for r in rows]
    if q:
        ingredients = [i for i in ingredients if q in i["name"].lower()]

    if g.user:
        selected_rows = db.execute(
            "SELECT ingredient_id FROM pantry_items WHERE user_id = ?",
            (g.user["id"],),
        ).fetchall()
        selected_ids = {r["ingredient_id"] for r in selected_rows}
    else:
        selected_ids = _get_selected_ids()

    return render_template(
        "pantry/ingredients.html",
        ingredients=ingredients,
        selected_ids=selected_ids,
        q=q,
    )


@bp.post("/ingredients/toggle")
def toggle_ingredient():
    ingredient_id = int(request.form["ingredient_id"])
    db = get_db()

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
        else:
            selected.add(ingredient_id)
        _set_selected_ids(selected)

    return redirect(url_for("pantry.ingredients"))
