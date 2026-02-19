# Pantry Planner (Flask + SQLite + TheMealDB)

Pantry Planner lets users select ingredients they have and discover recipes powered by TheMealDB API. Logged-in users can save their pantry, bookmark recipes, and maintain a persistent grocery list (with a print-friendly view).

## Features
- Ingredient browser + search
- “Find Recipes” with:
  - **Partial** match mode (recipes matching at least N selected ingredients)
  - **Strict** match mode (recipes matching ALL selected ingredients)
- Accounts (register/login/logout) to persist pantry selections
- Bookmarks (save recipes to revisit later)
- Grocery list (add/check/delete/clear) + print-friendly view
- Admin panel (admin-only) to sync ingredients from TheMealDB

## Tech Stack
- Python + Flask
- SQLite
- TheMealDB API


## Using Pantry Planner
Ingredients

Go to /ingredients

Select ingredients (Add/Remove)

Logged-in users: selections persist in the database

Anonymous users: selections persist only in the browser session

Find Recipes

Go to /recipes/search

Partial matching: mode=partial with a minimum match count:

Example: /recipes/search?mode=partial&min=2

Strict matching: mode=all (requires ALL selected ingredients):

Example: /recipes/search?mode=all

Bookmarks

Go to /bookmarks

You must be logged in to bookmark recipes.

Grocery List

Go to /grocery/ (logged-in users only)

Print view: /grocery/print
---

## Quickstart

### 1) Clone the repo
```bash
git clone https://github.com/PiFusion/Pantry-Planner.git
cd Pantry-Planner


### v2) Create & activate a virtual environment
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

### 3) Install the Dependencies
pip install -r requirements.txt

Initialize the Database + Ingredient Cache
1) Create the SQLite DB + tables
flask --app pantry_planner init-db
2) Pull ingredient list from TheMealDB into SQLite
flask --app pantry_planner sync-ingredients

Run the App
flask --app pantry_planner run

Open:

http://127.0.0.1:5000/ingredients







---

## How to end the venv (and cool the laptop down)

1) **Stop Flask** (in the terminal running it): press **Ctrl + C**.  
2) **Deactivate venv**:
```bash
deactivate
