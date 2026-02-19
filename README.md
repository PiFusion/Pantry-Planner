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

## Notes
- Use **Find Recipes** with `match=any` (default) for partial ingredient matches, or switch to strict mode for all-ingredient matches.
- Bookmark recipes from results or detail pages.
- Logged-in users can manage a persistent **Grocery List** at `/grocery/`, including print-friendly output at `/grocery/print`.

## If GitHub says your PR has conflicts
Use the command line from your PR branch:

```bash
git fetch origin
git checkout <your-pr-branch>
git merge origin/main
./scripts/resolve_pr_conflicts.sh
git commit -m "Resolve PR conflicts"
git push
```

The helper script keeps the feature branch versions of the known conflicting files and checks for leftover conflict markers.

