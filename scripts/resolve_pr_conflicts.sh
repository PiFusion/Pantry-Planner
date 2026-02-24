#!/usr/bin/env bash
set -euo pipefail

# Run from repo root. This script keeps the feature-rich branch versions
# for the files that commonly conflict with main in this project.

FILES=(
  README.md
  pantry_planner/__init__.py
  pantry_planner/bookmarks.py
  pantry_planner/recipes.py
  pantry_planner/templates/base.html
  pantry_planner/templates/recipes/results.html
  schema.sql
)

for f in "${FILES[@]}"; do
  git checkout --ours "$f"
  git add "$f"
done

if rg -n "<<<<<<<|=======|>>>>>>>" "${FILES[@]}" >/dev/null 2>&1; then
  echo "Conflict markers still present. Resolve manually."
  exit 1
fi

echo "Conflicts staged for the target files."
echo "Now run: git commit -m 'Resolve PR conflicts by keeping feature branch versions'"
