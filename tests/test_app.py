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

    def test_recipe_search_supports_legacy_mode_alias(self):
        with self.app.app_context():
            db = get_db()
            db.execute("INSERT INTO ingredients (id, name, hidden) VALUES (1, 'Chicken', 0)")
            db.commit()

        with self.client.session_transaction() as sess:
            sess["selected_ingredient_ids"] = [1]

        with patch("pantry_planner.recipes.filter_meals_by_ingredient", return_value=[]):
            r = self.client.get("/recipes/search?mode=strict", follow_redirects=False)

        text = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("<option value=\"all\" selected>", text)

    def test_admin_panel_can_show_all_blacklist_matches(self):
        self._create_user("admin@example.com", role="admin")
        self._login("admin@example.com")

        with self.app.app_context():
            db = get_db()
            for i in range(110):
                db.execute("INSERT INTO ingredients (name, hidden) VALUES (?, 0)", (f"Ingredient{i:03d}",))
            db.commit()

        limited = self.client.get("/admin/", follow_redirects=False)
        limited_text = limited.get_data(as_text=True)
        self.assertIn("Showing 100 of 110 matching ingredient(s)", limited_text)

        expanded = self.client.get("/admin/?show_all_ingredients=1", follow_redirects=False)
        expanded_text = expanded.get_data(as_text=True)
        self.assertIn("Showing 110 of 110 matching ingredient(s)", expanded_text)

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


if __name__ == "__main__":
    unittest.main()
