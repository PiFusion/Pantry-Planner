import requests

BASE = "https://www.themealdb.com/api/json/v1/1"


def _get(url: str, params=None):
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def fetch_ingredients():
    """
    Endpoint: list.php?i=list
    Returns list of dicts: {name, mealdb_id}
    """
    data = _get(f"{BASE}/list.php", params={"i": "list"})
    meals = data.get("meals") or []
    out = []
    for item in meals:
        name = (item.get("strIngredient") or "").strip()
        if not name:
            continue
        mealdb_id = item.get("idIngredient")
        out.append({"name": name, "mealdb_id": int(mealdb_id) if mealdb_id else None})
    return out


def filter_meals_by_ingredient(ingredient_name: str):
    """
    Endpoint: filter.php?i=Chicken
    Returns: list of meals: {idMeal, strMeal, strMealThumb}
    """
    data = _get(f"{BASE}/filter.php", params={"i": ingredient_name})
    return data.get("meals") or []


def lookup_meal(meal_id: str):
    """
    Endpoint: lookup.php?i=52772
    Returns dict meal details
    """
    data = _get(f"{BASE}/lookup.php", params={"i": meal_id})
    meals = data.get("meals") or []
    return meals[0] if meals else None
