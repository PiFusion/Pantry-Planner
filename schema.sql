PRAGMA foreign_keys = ON;

BEGIN;

-- Users
CREATE TABLE IF NOT EXISTS users (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  username      TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  role          TEXT NOT NULL DEFAULT 'user',         -- 'user' or 'admin'
  created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Cached ingredient list from MealDB (your app reads ingredients from here)
CREATE TABLE IF NOT EXISTS ingredients (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  mealdb_id   INTEGER,
  name        TEXT NOT NULL UNIQUE,
  hidden      INTEGER NOT NULL DEFAULT 0,
  updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Pantry selections per user (many-to-many)
CREATE TABLE IF NOT EXISTS pantry_items (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id       INTEGER NOT NULL,
  ingredient_id INTEGER NOT NULL,
  expires_on    TEXT,
  added_on      TEXT,
  created_at    TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, ingredient_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE
);

-- Bookmarked MealDB recipes per user
CREATE TABLE IF NOT EXISTS bookmarks (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id        INTEGER NOT NULL,
  mealdb_meal_id TEXT NOT NULL,                       -- MealDB "idMeal"
  meal_name      TEXT,                                -- optional cache for display
  meal_thumb     TEXT,                                -- optional cache for display
  created_at     TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, mealdb_meal_id),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Optional: cache meal JSON to reduce API calls
CREATE TABLE IF NOT EXISTS meal_cache (
  mealdb_meal_id TEXT PRIMARY KEY,
  json           TEXT NOT NULL,
  cached_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Grocery list items per user
CREATE TABLE IF NOT EXISTS grocery_items (
  id                       INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id                  INTEGER NOT NULL,
  item_name                TEXT NOT NULL,
  quantity                 TEXT,
  quantity_amount          REAL,
  quantity_unit            TEXT,
  quantity_unit_normalized TEXT,
  quantity_parse_status    TEXT,
  notes                    TEXT,
  is_checked               INTEGER NOT NULL DEFAULT 0,
  created_at               TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Meal planning by week
CREATE TABLE IF NOT EXISTS meal_plans (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL,
  week_start  TEXT NOT NULL,
  created_at  TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(user_id, week_start),
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

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
);

COMMIT;

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_pantry_user ON pantry_items(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user ON bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_ingredients_hidden ON ingredients(hidden);
CREATE INDEX IF NOT EXISTS idx_grocery_user ON grocery_items(user_id);

CREATE INDEX IF NOT EXISTS idx_pantry_expiry ON pantry_items(expires_on);
CREATE INDEX IF NOT EXISTS idx_meal_plans_user_week ON meal_plans(user_id, week_start);
CREATE INDEX IF NOT EXISTS idx_plan_entries_plan_day ON meal_plan_entries(plan_id, day_of_week);
