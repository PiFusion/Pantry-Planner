from datetime import date, datetime

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




def _ingredient_category(name: str) -> str:
    lower = (name or "").lower()
    spice_keywords = ("pepper", "spice", "cinnamon", "allspice", "paprika", "seasoning")
    if any(k in lower for k in spice_keywords):
        return "Spice"
    return "Pantry"


def _expiry_status(expires_on: str | None):
    if not expires_on:
        return None

    try:
        expiry_date = datetime.strptime(expires_on, "%Y-%m-%d").date()
    except ValueError:
        return {"kind": "neutral", "text": "Invalid date"}

    today = date.today()
    delta_days = (expiry_date - today).days

    if delta_days < 0:
        days_ago = abs(delta_days)
        label = "day" if days_ago == 1 else "days"
        return {"kind": "expired", "text": f"Expired {days_ago} {label} ago"}

    if delta_days <= 3:
        label = "day" if delta_days == 1 else "days"
        return {"kind": "soon", "text": f"Expires in {delta_days} {label}"}

    pretty = expiry_date.strftime("%b %d, %Y").replace(" 0", " ")
    return {"kind": "fresh", "text": f"Expires {pretty}"}


def _load_filtered_ingredients(q: str):
    db = get_db()
    params = []
    where = "WHERE hidden = 0"
    if q:
        where += " AND lower(name) LIKE ?"
        params.append(f"%{q}%")

    rows = db.execute(
        f"SELECT id, name FROM ingredients {where} ORDER BY name",
        params,
    ).fetchall()
    return [{"id": r["id"], "name": r["name"]} for r in rows]


def _selected_ingredients_for_current_user():
    db = get_db()

    if g.user:
        rows = db.execute(
            """
            SELECT i.id, i.name, p.expires_on
            FROM pantry_items p
            JOIN ingredients i ON i.id = p.ingredient_id
            WHERE p.user_id = ? AND i.hidden = 0
            ORDER BY i.name
            """,
            (g.user["id"],),
        ).fetchall()
        selected_ingredients = [
            {
                "id": r["id"],
                "name": r["name"],
                "expires_on": r["expires_on"],
                "category": _ingredient_category(r["name"]),
                "expiry_status": _expiry_status(r["expires_on"]),
            }
            for r in rows
        ]
        selected_ids = {r["id"] for r in rows}
        return selected_ingredients, selected_ids

    selected_ids = _get_selected_ids()
    if not selected_ids:
        return [], set()

    placeholders = ",".join(["?"] * len(selected_ids))
    rows = db.execute(
        f"""
        SELECT id, name
        FROM ingredients
        WHERE hidden = 0 AND id IN ({placeholders})
        ORDER BY name
        """,
        list(selected_ids),
    ).fetchall()

    selected_ingredients = [{
        "id": r["id"],
        "name": r["name"],
        "expires_on": None,
        "category": _ingredient_category(r["name"]),
        "expiry_status": None,
    } for r in rows]
    normalized_ids = {r["id"] for r in rows}
    return selected_ingredients, normalized_ids


@bp.get("/ingredients")
def ingredients():
    q = request.args.get("q", "").strip().lower()
    filtered_ingredients = _load_filtered_ingredients(q)
    selected_ingredients, selected_ids = _selected_ingredients_for_current_user()

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
                "INSERT INTO pantry_items (user_id, ingredient_id, added_on) VALUES (?, ?, date('now'))",
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

    action, ingredient_name = _toggle_by_id(ingredient_id)
    selected_count = len(_selected_ingredients_for_current_user()[1])

    return jsonify({
        "ok": True,
        "action": action,
        "ingredient_id": ingredient_id,
        "ingredient_name": ingredient_name,
        "selected_count": selected_count,
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

    return jsonify({"ok": True, "selected_count": 0})


@bp.post("/ingredients/expiry/<int:ingredient_id>")
def update_expiry(ingredient_id):
    if g.user is None:
        return redirect(url_for("auth.login"))

    expires_on = (request.form.get("expires_on") or "").strip()
    if not expires_on:
        expires_on = None

    db = get_db()
    db.execute(
        """
        UPDATE pantry_items
        SET expires_on = ?
        WHERE user_id = ? AND ingredient_id = ?
        """,
        (expires_on, g.user["id"], ingredient_id),
    )
    db.commit()

    return redirect(url_for("pantry.ingredients", q=request.form.get("return_q", "")))
