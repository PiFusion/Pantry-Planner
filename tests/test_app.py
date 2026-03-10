import os
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
