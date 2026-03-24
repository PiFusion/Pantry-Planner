import os
import tempfile
import unittest
from unittest.mock import patch

from werkzeug.security import generate_password_hash

from pantry_planner import create_app
from pantry_planner.db import get_db, init_db


class PantryPlannerTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test.sqlite")

        self.app = create_app()
        self.app.config.update(
            TESTING=True,
            DATABASE=self.db_path,
            SECRET_KEY="test-secret",
        )

        with self.app.app_context():
            init_db()

        self.client = self.app.test_client()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_user(self, username="user@example.com", password="pass", role="user"):
        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, generate_password_hash(password), role),
            )
            db.commit()
            return db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()["id"]

    def _login(self, username="user@example.com", password="pass"):
        return self.client.post(
            "/auth/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_register_and_login_flow(self):
        r = self.client.post(
            "/auth/register",
            data={"username": "a@b.com", "password": "pw"},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)

        r = self.client.post(
            "/auth/login",
            data={"username": "a@b.com", "password": "pw"},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn("/ingredients", r.headers["Location"])

    def test_admin_blocked_for_non_admin(self):
        self._create_user()
        self._login()

        r = self.client.get("/admin/", follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn("/ingredients", r.headers["Location"])

    def test_pantry_toggle_for_logged_in_user(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES (?, 0)", ("Chicken",))
            ing_id = db.execute("SELECT id FROM ingredients WHERE name = ?", ("Chicken",)).fetchone()["id"]
            db.commit()

        self.client.post("/ingredients/toggle", data={"ingredient_id": ing_id}, follow_redirects=False)

        with self.app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT 1 FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (uid, ing_id),
            ).fetchone()
            self.assertIsNotNone(row)

    def test_blacklisted_ingredient_hidden_on_ingredients_page(self):
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Visible', 0)")
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('HiddenOne', 1)")
            db.commit()

        r = self.client.get("/ingredients")
        text = r.get_data(as_text=True)
        self.assertIn("Visible", text)
        self.assertNotIn("HiddenOne", text)

    def test_grocery_add_and_remove(self):
        uid = self._create_user()
        self._login()

        self.client.post(
            "/grocery/add",
            data={"item_name": "Milk", "quantity": "1", "notes": "2%"},
            follow_redirects=False,
        )

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                "SELECT id, item_name FROM grocery_items WHERE user_id = ?",
                (uid,),
            ).fetchone()
            self.assertIsNotNone(item)
            item_id = item["id"]

        self.client.post(f"/grocery/delete/{item_id}", follow_redirects=False)

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                "SELECT id FROM grocery_items WHERE user_id = ?",
                (uid,),
            ).fetchone()
            self.assertIsNone(item)

    def test_add_from_ingredients_stays_on_ingredients_page(self):
        uid = self._create_user()
        self._login()

        r = self.client.post(
            "/grocery/add-from-ingredients",
            data={
                "item_name": "Tomato",
                "quantity": "3",
                "notes": "roma",
                "return_q": "tom",
            },
            follow_redirects=False,
        )

        self.assertEqual(r.status_code, 302)
        self.assertIn("/ingredients?q=tom", r.headers["Location"])

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                "SELECT item_name, quantity, notes FROM grocery_items WHERE user_id = ?",
                (uid,),
            ).fetchone()
            self.assertIsNotNone(item)
            self.assertEqual(item["item_name"], "Tomato")
            self.assertEqual(item["quantity"], "3")
            self.assertEqual(item["notes"], "roma")

    def test_clear_checked_only_removes_checked_items(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO grocery_items (user_id, item_name, is_checked) VALUES (?, ?, 1)",
                (uid, "Done item"),
            )
            db.execute(
                "INSERT INTO grocery_items (user_id, item_name, is_checked) VALUES (?, ?, 0)",
                (uid, "Todo item"),
            )
            db.commit()

        r = self.client.post('/grocery/clear-checked', follow_redirects=False)
        self.assertEqual(r.status_code, 302)
        self.assertIn('/grocery/', r.headers['Location'])

        with self.app.app_context():
            db = get_db()
            rows = db.execute(
                "SELECT item_name, is_checked FROM grocery_items WHERE user_id = ? ORDER BY item_name",
                (uid,),
            ).fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['item_name'], 'Todo item')
            self.assertEqual(rows[0]['is_checked'], 0)

    def test_grocery_page_shows_autocomplete_ingredient_matches(self):
        self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Bacon', 0)")
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Milk', 0)")
            db.commit()

        r = self.client.get('/grocery/?ingredient_q=ba')
        text = r.get_data(as_text=True)

        self.assertEqual(r.status_code, 200)
        self.assertIn('Search or add item name', text)
        self.assertIn('Bacon', text)
        self.assertIn('<span>Bacon</span>', text)
        self.assertNotIn('<span>Milk</span>', text)


    def test_grocery_item_update_edits_quantity_and_notes(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO grocery_items (user_id, item_name, quantity, notes) VALUES (?, ?, ?, ?)",
                (uid, "Bread", "1 loaf", "old"),
            )
            item_id = db.execute(
                "SELECT id FROM grocery_items WHERE user_id = ? AND item_name = ?",
                (uid, "Bread"),
            ).fetchone()["id"]
            db.commit()

        r = self.client.post(
            f"/grocery/update/{item_id}",
            data={"quantity": "2 loaves", "notes": "whole wheat"},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)
        self.assertIn('/grocery/', r.headers['Location'])

        with self.app.app_context():
            db = get_db()
            updated = db.execute(
                "SELECT quantity, notes FROM grocery_items WHERE id = ? AND user_id = ?",
                (item_id, uid),
            ).fetchone()
            self.assertEqual(updated['quantity'], '2 loaves')
            self.assertEqual(updated['notes'], 'whole wheat')

    def test_grocery_print_view_renders_without_platform_specific_strftime(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO grocery_items (user_id, item_name, quantity, notes) VALUES (?, ?, ?, ?)",
                (uid, 'Chicken', '2', 'sale'),
            )
            db.commit()

        r = self.client.get('/grocery/print')
        text = r.get_data(as_text=True)

        self.assertEqual(r.status_code, 200)
        self.assertIn('Printed:', text)
        self.assertIn('Chicken', text)

    def test_toggle_ingredient_async_returns_lightweight_payload(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES (?, 0)", ("Onion",))
            ing_id = db.execute("SELECT id FROM ingredients WHERE name = ?", ("Onion",)).fetchone()["id"]
            db.commit()

        r = self.client.post('/ingredients/toggle-async', data={"ingredient_id": ing_id, "return_q": ""})
        payload = r.get_json()

        self.assertEqual(r.status_code, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["action"], "added")
        self.assertEqual(payload["ingredient_id"], ing_id)
        self.assertEqual(payload["ingredient_name"], "Onion")
        self.assertEqual(payload["selected_count"], 1)
        self.assertNotIn("selected_ids", payload)
        self.assertNotIn("selected_ingredients", payload)

        with self.app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT 1 FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (uid, ing_id),
            ).fetchone()
            self.assertIsNotNone(row)

    def test_add_from_ingredients_async_supports_quantity_unit_and_notes(self):
        uid = self._create_user()
        self._login()

        r = self.client.post(
            '/grocery/add-from-ingredients-async',
            data={
                'item_name': 'Tomato',
                'quantity': '2',
                'unit': 'lb',
                'notes': 'roma',
                'return_q': 'tom',
            },
        )
        payload = r.get_json()

        self.assertEqual(r.status_code, 200)
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['item_name'], 'Tomato')

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                "SELECT item_name, quantity, notes FROM grocery_items WHERE user_id = ?",
                (uid,),
            ).fetchone()
            self.assertIsNotNone(item)
            self.assertEqual(item['item_name'], 'Tomato')
            self.assertEqual(item['quantity'], '2 lb')
            self.assertEqual(item['notes'], 'roma')

    def test_pantry_expiry_update_sets_date_for_selected_ingredient(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Lettuce', 0)")
            ingredient_id = db.execute("SELECT id FROM ingredients WHERE name = 'Lettuce'").fetchone()["id"]
            db.execute(
                "INSERT INTO pantry_items (user_id, ingredient_id) VALUES (?, ?)",
                (uid, ingredient_id),
            )
            db.commit()

        r = self.client.post(
            f"/ingredients/expiry/{ingredient_id}",
            data={"expires_on": "2026-04-01", "return_q": ""},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT expires_on FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (uid, ingredient_id),
            ).fetchone()
            self.assertEqual(row["expires_on"], "2026-04-01")

    def test_meal_plan_generate_grocery_merges_quantity_units(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO meal_plans (user_id, week_start) VALUES (?, ?)",
                (uid, "2026-03-23"),
            )
            plan_id = db.execute(
                "SELECT id FROM meal_plans WHERE user_id = ? AND week_start = ?",
                (uid, "2026-03-23"),
            ).fetchone()["id"]
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 0, 'dinner', '101', 'Meal A')
                """,
                (plan_id,),
            )
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 1, 'dinner', '102', 'Meal B')
                """,
                (plan_id,),
            )
            db.commit()

        fake_meals = {
            "101": {"strIngredient1": "Chicken", "strMeasure1": "2 lb"},
            "102": {"strIngredient1": "Chicken", "strMeasure1": "1 lb"},
        }

        with patch("pantry_planner.planner.lookup_meal", side_effect=lambda meal_id: fake_meals.get(meal_id)):
            r = self.client.post(
                "/planner/generate-grocery?week_start=2026-03-23",
                data={"day_of_week": ["0", "1"]},
                follow_redirects=False,
            )

        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                """
                SELECT item_name, quantity, quantity_amount, quantity_unit
                FROM grocery_items
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (uid,),
            ).fetchone()
            self.assertEqual(item["item_name"], "Chicken")
            self.assertEqual(item["quantity"], "3 lb")
            self.assertEqual(item["quantity_amount"], 3.0)
            self.assertEqual(item["quantity_unit"], "lb")



    def test_runtime_migration_adds_missing_columns_for_existing_db(self):
        legacy_db_path = os.path.join(self.temp_dir.name, "legacy.sqlite")
        conn = __import__("sqlite3").connect(legacy_db_path)
        conn.executescript(
            """
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, role TEXT, created_at TEXT);
            CREATE TABLE ingredients (id INTEGER PRIMARY KEY, name TEXT, hidden INTEGER, updated_at TEXT);
            CREATE TABLE pantry_items (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, ingredient_id INTEGER NOT NULL, created_at TEXT);
            CREATE TABLE grocery_items (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, item_name TEXT NOT NULL, quantity TEXT, notes TEXT, is_checked INTEGER, created_at TEXT);
            """
        )
        conn.commit()
        conn.close()

        legacy_app = create_app()
        legacy_app.config.update(TESTING=True, DATABASE=legacy_db_path, SECRET_KEY="legacy")

        with legacy_app.app_context():
            db = get_db()
            pantry_cols = {r[1] for r in db.execute("PRAGMA table_info(pantry_items)").fetchall()}
            grocery_cols = {r[1] for r in db.execute("PRAGMA table_info(grocery_items)").fetchall()}
            planner_table = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meal_plans'"
            ).fetchone()

            self.assertIn("expires_on", pantry_cols)
            self.assertIn("added_on", pantry_cols)
            self.assertIn("quantity_amount", grocery_cols)
            self.assertIn("quantity_unit", grocery_cols)
            self.assertIsNotNone(planner_table)

    def test_pantry_expiry_update_sets_date_for_selected_ingredient(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Lettuce', 0)")
            ingredient_id = db.execute("SELECT id FROM ingredients WHERE name = 'Lettuce'").fetchone()["id"]
            db.execute(
                "INSERT INTO pantry_items (user_id, ingredient_id) VALUES (?, ?)",
                (uid, ingredient_id),
            )
            db.commit()

        r = self.client.post(
            f"/ingredients/expiry/{ingredient_id}",
            data={"expires_on": "2026-04-01", "return_q": ""},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT expires_on FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (uid, ingredient_id),
            ).fetchone()
            self.assertEqual(row["expires_on"], "2026-04-01")

    def test_meal_plan_generate_grocery_merges_quantity_units(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO meal_plans (user_id, week_start) VALUES (?, ?)",
                (uid, "2026-03-23"),
            )
            plan_id = db.execute(
                "SELECT id FROM meal_plans WHERE user_id = ? AND week_start = ?",
                (uid, "2026-03-23"),
            ).fetchone()["id"]
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 0, 'dinner', '101', 'Meal A')
                """,
                (plan_id,),
            )
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 1, 'dinner', '102', 'Meal B')
                """,
                (plan_id,),
            )
            db.commit()

        fake_meals = {
            "101": {"strIngredient1": "Chicken", "strMeasure1": "2 lb"},
            "102": {"strIngredient1": "Chicken", "strMeasure1": "1 lb"},
        }

        with patch("pantry_planner.planner.lookup_meal", side_effect=lambda meal_id: fake_meals.get(meal_id)):
            r = self.client.post(
                "/planner/generate-grocery?week_start=2026-03-23",
                data={"day_of_week": ["0", "1"]},
                follow_redirects=False,
            )

        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                """
                SELECT item_name, quantity, quantity_amount, quantity_unit
                FROM grocery_items
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (uid,),
            ).fetchone()
            self.assertEqual(item["item_name"], "Chicken")
            self.assertEqual(item["quantity"], "3 lb")
            self.assertEqual(item["quantity_amount"], 3.0)
            self.assertEqual(item["quantity_unit"], "lb")



    def test_runtime_migration_adds_missing_columns_for_existing_db(self):
        legacy_db_path = os.path.join(self.temp_dir.name, "legacy.sqlite")
        conn = __import__("sqlite3").connect(legacy_db_path)
        conn.executescript(
            """
            CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, role TEXT, created_at TEXT);
            CREATE TABLE ingredients (id INTEGER PRIMARY KEY, name TEXT, hidden INTEGER, updated_at TEXT);
            CREATE TABLE pantry_items (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, ingredient_id INTEGER NOT NULL, created_at TEXT);
            CREATE TABLE grocery_items (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, item_name TEXT NOT NULL, quantity TEXT, notes TEXT, is_checked INTEGER, created_at TEXT);
            """
        )
        conn.commit()
        conn.close()

        legacy_app = create_app()
        legacy_app.config.update(TESTING=True, DATABASE=legacy_db_path, SECRET_KEY="legacy")

        with legacy_app.app_context():
            db = get_db()
            pantry_cols = {r[1] for r in db.execute("PRAGMA table_info(pantry_items)").fetchall()}
            grocery_cols = {r[1] for r in db.execute("PRAGMA table_info(grocery_items)").fetchall()}
            planner_table = db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='meal_plans'"
            ).fetchone()

            self.assertIn("expires_on", pantry_cols)
            self.assertIn("added_on", pantry_cols)
            self.assertIn("quantity_amount", grocery_cols)
            self.assertIn("quantity_unit", grocery_cols)
            self.assertIsNotNone(planner_table)

    def test_pantry_expiry_update_sets_date_for_selected_ingredient(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (name, hidden) VALUES ('Lettuce', 0)")
            ingredient_id = db.execute("SELECT id FROM ingredients WHERE name = 'Lettuce'").fetchone()["id"]
            db.execute(
                "INSERT INTO pantry_items (user_id, ingredient_id) VALUES (?, ?)",
                (uid, ingredient_id),
            )
            db.commit()

        r = self.client.post(
            f"/ingredients/expiry/{ingredient_id}",
            data={"expires_on": "2026-04-01", "return_q": ""},
            follow_redirects=False,
        )
        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            row = db.execute(
                "SELECT expires_on FROM pantry_items WHERE user_id = ? AND ingredient_id = ?",
                (uid, ingredient_id),
            ).fetchone()
            self.assertEqual(row["expires_on"], "2026-04-01")


    def test_planner_page_includes_breakfast_slot(self):
        self._create_user()
        self._login()

        r = self.client.get('/planner/?week_start=2026-03-23')
        text = r.get_data(as_text=True)

        self.assertEqual(r.status_code, 200)
        self.assertIn('Save breakfast', text)

    def test_meal_plan_generate_grocery_merges_quantity_units(self):
        uid = self._create_user()
        self._login()

        with self.app.app_context():
            db = get_db()
            db.execute(
                "INSERT INTO meal_plans (user_id, week_start) VALUES (?, ?)",
                (uid, "2026-03-23"),
            )
            plan_id = db.execute(
                "SELECT id FROM meal_plans WHERE user_id = ? AND week_start = ?",
                (uid, "2026-03-23"),
            ).fetchone()["id"]
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 0, 'dinner', '101', 'Meal A')
                """,
                (plan_id,),
            )
            db.execute(
                """
                INSERT INTO meal_plan_entries (plan_id, day_of_week, meal_slot, mealdb_meal_id, meal_name)
                VALUES (?, 1, 'dinner', '102', 'Meal B')
                """,
                (plan_id,),
            )
            db.commit()

        fake_meals = {
            "101": {"strIngredient1": "Chicken", "strMeasure1": "2 lb"},
            "102": {"strIngredient1": "Chicken", "strMeasure1": "1 lb"},
        }

        with patch("pantry_planner.planner.lookup_meal", side_effect=lambda meal_id: fake_meals.get(meal_id)):
            r = self.client.post(
                "/planner/generate-grocery?week_start=2026-03-23",
                data={"day_of_week": ["0", "1"]},
                follow_redirects=False,
            )

        self.assertEqual(r.status_code, 302)

        with self.app.app_context():
            db = get_db()
            item = db.execute(
                """
                SELECT item_name, quantity, quantity_amount, quantity_unit
                FROM grocery_items
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (uid,),
            ).fetchone()
            self.assertEqual(item["item_name"], "Chicken")
            self.assertEqual(item["quantity"], "3 lb")
            self.assertEqual(item["quantity_amount"], 3.0)
            self.assertEqual(item["quantity_unit"], "lb")



if __name__ == "__main__":
    unittest.main()
