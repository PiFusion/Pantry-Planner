# Pantry Planner (Flask + SQLite + MealDB)

## Setup
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

pip install -r requirements.txt
```

## Initialize DB
```bash
flask --app pantry_planner init-db
flask --app pantry_planner sync-ingredients
```

## Run
```bash
flask --app pantry_planner run --debug
```
