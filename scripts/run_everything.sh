#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -d ".venv" ]]; then
  python -m venv .venv
fi

source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

flask --app pantry_planner init-db
flask --app pantry_planner sync-ingredients

PYTHONPATH=. pytest -q

if [[ "${1:-}" == "--serve" ]]; then
  flask --app pantry_planner run --debug
else
  cat <<'EOF'

All setup + tests completed successfully.
Start the app with:
  flask --app pantry_planner run --debug
EOF
fi
