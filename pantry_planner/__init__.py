from flask import Flask, render_template
import os
import logging
from sentry_sdk import add_breadcrumb
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration
from .db import close_db, init_db, get_db
from .integrations.mealdb import fetch_ingredients

# Load env vars
load_dotenv()


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    sentry_logging = LoggingIntegration(
        level="INFO",        # logs become breadcrumbs
        event_level="ERROR"  # errors become events
    )

    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FlaskIntegration(), sentry_logging],
        traces_sample_rate=1.0,
    )
    print("SENTRY DSN:", os.getenv("SENTRY_DSN"))

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-secret-change-me"),
        DATABASE=os.path.join(app.instance_path, "pantry_planner.sqlite"),
    )

    os.makedirs(app.instance_path, exist_ok=True)

    app.teardown_appcontext(close_db)

    # CLI: init db
    @app.cli.command("init-db")
    def init_db_command():
        init_db()
        print("✅ Database initialized.")

    # CLI: sync ingredients
    @app.cli.command("sync-ingredients")
    def sync_ingredients_command():
        db = get_db()

        add_breadcrumb(
            category="sync",
            message="Fetching ingredients from MealDB",
            level="info"
        )
        items = fetch_ingredients()

        add_breadcrumb(
            category="sync",
            message=f"Fetched {len(items)} ingredients, beginning DB upsert",
            level="info"
        )
        for ing in items:
            db.execute(
                """
                INSERT INTO ingredients (name, mealdb_id, updated_at)
                VALUES (?, ?, datetime('now'))
                ON CONFLICT(name) DO UPDATE SET
                  mealdb_id = excluded.mealdb_id,
                  updated_at = datetime('now')
                """,
                (ing["name"], ing.get("mealdb_id")),
            )

        db.commit()
        print(f"✅ Synced {len(items)} ingredients.")

    # CLI: make admin
    @app.cli.command("make-admin")
    def make_admin_command():
        import click

        username = click.prompt("Username to promote").strip()

        add_breadcrumb(
            category="admin",
            message=f"Attempting to promote user to admin: {username}",
            level="info"
        )

        db = get_db()
        user = db.execute(
            "SELECT id, role FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if not user:
            print("❌ User not found")
            return

        if user["role"] == "admin":
            print("ℹ️ Already admin")
            return

        add_breadcrumb(
            category="admin",
            message=f"Executing role update for user id: {user['id']}",
            level="info"
        )
        db.execute(
            "UPDATE users SET role = 'admin' WHERE id = ?",
            (user["id"],)
        )
        db.commit()
        print("✅ Promoted to admin")

    # Blueprints
    from .auth import bp as auth_bp
    from .pantry import bp as pantry_bp
    from .recipes import bp as recipes_bp
    from .bookmarks import bp as bookmarks_bp
    from .admin import bp as admin_bp
    from .grocery import bp as grocery_bp
    from .planner import bp as planner_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(pantry_bp)
    app.register_blueprint(recipes_bp)
    app.register_blueprint(bookmarks_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(grocery_bp)
    app.register_blueprint(planner_bp)

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/sentry-test")
    def sentry_test():
        logging.info("Log before crash")

        add_breadcrumb(
            category="test",
            message="Manual breadcrumb before crash",
            level="info"
        )

        raise Exception("Sentry is working!")

    return app