import sqlite3
from pathlib import Path
from flask import current_app, g


def _table_columns(db: sqlite3.Connection, table_name: str) -> set[str]:
    rows = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def _table_exists(db: sqlite3.Connection, table_name: str) -> bool:
    row = db.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _ensure_runtime_migrations(db: sqlite3.Connection):
    # pantry_items additions
    pantry_cols = _table_columns(db, "pantry_items")
    if "expires_on" not in pantry_cols:
        db.execute("ALTER TABLE pantry_items ADD COLUMN expires_on TEXT")
    if "added_on" not in pantry_cols:
        db.execute("ALTER TABLE pantry_items ADD COLUMN added_on TEXT")

    # grocery_items additions
    grocery_cols = _table_columns(db, "grocery_items")
    if "quantity_amount" not in grocery_cols:
        db.execute("ALTER TABLE grocery_items ADD COLUMN quantity_amount REAL")
    if "quantity_unit" not in grocery_cols:
        db.execute("ALTER TABLE grocery_items ADD COLUMN quantity_unit TEXT")
    if "quantity_unit_normalized" not in grocery_cols:
        db.execute("ALTER TABLE grocery_items ADD COLUMN quantity_unit_normalized TEXT")
    if "quantity_parse_status" not in grocery_cols:
        db.execute("ALTER TABLE grocery_items ADD COLUMN quantity_parse_status TEXT")

    # planner tables
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_plans (
          id          INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id     INTEGER NOT NULL,
          week_start  TEXT NOT NULL,
          created_at  TEXT NOT NULL DEFAULT (datetime('now')),
          UNIQUE(user_id, week_start),
          FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS meal_plan_entries (
          id             INTEGER PRIMARY KEY AUTOINCREMENT,
          plan_id        INTEGER NOT NULL,
          day_of_week    INTEGER NOT NULL,
          meal_slot      TEXT NOT NULL,
          mealdb_meal_id TEXT NOT NULL,
          meal_name      TEXT,
          meal_thumb     TEXT,
          created_at     TEXT NOT NULL DEFAULT (datetime('now')),
          UNIQUE(plan_id, day_of_week, meal_slot),
          FOREIGN KEY (plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
        )
        """
    )

    # supportive indexes
    db.execute("CREATE INDEX IF NOT EXISTS idx_pantry_expiry ON pantry_items(expires_on)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_meal_plans_user_week ON meal_plans(user_id, week_start)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_plan_entries_plan_day ON meal_plan_entries(plan_id, day_of_week)")

    db.commit()


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(current_app.config["DATABASE"])
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn

        # Upgrade older local databases in-place when app boots.
        if _table_exists(conn, "pantry_items") and _table_exists(conn, "grocery_items"):
            _ensure_runtime_migrations(conn)
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
