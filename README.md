# Pantry Planner (Flask + SQLite + TheMealDB)

Pantry Planner helps users select ingredients they already have and discover recipes powered by TheMealDB API.

## Features
- Ingredient browser with search (`/ingredients`)
- Recipe discovery (`/recipes/search`) with:
  - **Partial mode**: `?match=any` (default), with `min` threshold
  - **Strict mode**: `?match=all` (must match all selected ingredients)
  - Sort options: `?sort=match` or `?sort=name`
- User accounts (`/auth/register`, `/auth/login`, `/auth/logout`)
- Bookmarks (`/bookmarks/`) for logged-in users
- Grocery list (`/grocery/`) with check/uncheck/delete/clear and print view (`/grocery/print`)
- Admin panel (`/admin/`) for ingredient sync, user management, pantry edits, and ingredient blacklist controls (admin role required)

## Tech Stack
- Python + Flask
- SQLite
- TheMealDB API

## Quickstart

### 1) Clone
```bash
git clone https://github.com/PiFusion/Pantry-Planner.git
cd Pantry-Planner
```

### 2) Create and activate a virtual environment
```bash
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Initialize DB + sync ingredients
```bash
flask --app pantry_planner init-db
flask --app pantry_planner sync-ingredients
```

### 5) Run
```bash
flask --app pantry_planner run --debug
```

Open:
- `http://127.0.0.1:5000/ingredients`

## Admin setup
By default, newly registered users are created with role `user`.
To access `/admin/`, promote your account once from CLI:

```bash
flask --app pantry_planner make-admin
```

Then enter the username you registered with (for example, `toby@demo.com`).

Admin destructive actions now include confirmation prompts in the UI. Deleting another admin requires typing that admin username in the prompt.

## Usage Notes
- Anonymous users can select ingredients, but those selections are stored in session only.
- Logged-in users get persistent pantry selections, bookmarks, and grocery list.
- The Grocery List nav link appears only when logged in.
- Admin tools include: delete users, edit a user pantry, and blacklist/unblacklist ingredients.

## Troubleshooting (merge conflicts)
If GitHub says your PR has conflicts, from your PR branch run:

```bash
git fetch origin
git checkout <your-pr-branch>
git merge origin/main
./scripts/resolve_pr_conflicts.sh
git commit -m "Resolve PR conflicts"
git push
```

## Stop the app / exit venv
1. Stop Flask with `Ctrl + C`
2. Deactivate venv:
```bash
deactivate
```


## Tests
Run the lightweight test suite:

```bash
python -m unittest discover -s tests -v
```
