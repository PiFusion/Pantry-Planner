import sqlite3
from pathlib import Path
from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()

    # Allow schema.sql either inside package folder or repo root
    schema_path = Path(current_app.root_path) / "schema.sql"
    if not schema_path.exists():
        schema_path = Path(current_app.root_path).parent / "schema.sql"

    if not schema_path.exists():
        raise FileNotFoundError("schema.sql not found (expected in repo root or pantry_planner/).")

    db.executescript(schema_path.read_text(encoding="utf-8"))
    db.commit()
