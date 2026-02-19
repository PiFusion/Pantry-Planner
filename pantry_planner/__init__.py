from flask import Flask
import os

from .db import close_db, init_db, get_db
from .integrations.mealdb import fetch_ingredients


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.path.join(app.instance_path, "pantry_planner.sqlite"),
    )

    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(close_db)

    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("✅ Database initialized.")

    @app.cli.command("sync-ingredients")
    def sync_ingredients_command():
        """Fetch ingredient list from MealDB and store in local DB."""
        db = get_db()
        items = fetch_ingredients()

        for ing in items:
            name = ing["name"]
            mealdb_id = ing.get("mealdb_id")

            db.execute(
                """
                INSERT INTO ingredients (name, mealdb_id, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(name) DO UPDATE SET
                  mealdb_id = excluded.mealdb_id,
                  updated_at = datetime('now')
                """,
                (name, mealdb_id),
            )

        db.commit()
        print(f"✅ Synced {len(items)} ingredients into SQLite.")

    # Blueprints
    from .auth import bp as auth_bp
    from .pantry import bp as pantry_bp
    from .recipes import bp as recipes_bp
    from .bookmarks import bp as bookmarks_bp
    from .admin import bp as admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pantry_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(bookmarks_bp)
    app.register_blueprint(admin_bp)

    @app.get("/")
    def home():
        return "<p>Pantry Planner is running. Go to <a href='/ingredients'>/ingredients</a></p>"

    return app
