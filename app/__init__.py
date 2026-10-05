import os
from functools import wraps

from flask import Flask, jsonify, request, send_from_directory

from . import db
from .auth_utils import AUTH_TOKEN, has_login_fields, has_valid_auth_token, normalize_credentials


def create_app(db_path=None):
    """Build the Flask app. Tests call this directly; `python -m app` calls it to serve."""
    app = Flask(__name__)  # serves app/static/ at /static/

    conn = db.connect(db_path or os.environ.get("APP_DB_PATH", "app.db"))
    db.init_db(conn, os.environ.get("DEFAULT_ADMIN_PASSWORD", "password"))
    app.config["DB"] = conn  # exposed so tests can close it

    def require_auth(view):
        """Decorator for routes that need the login cookie."""

        @wraps(view)
        def wrapper(*args, **kwargs):
            if not has_valid_auth_token(request.cookies.get("token")):
                return jsonify(error="unauthorized"), 401
            return view(*args, **kwargs)

        return wrapper

    @app.post("/api/login")
    def login():
        body = request.get_json(silent=True)
        if not has_login_fields(body):
            return jsonify(error="username and password are required"), 400
        creds = normalize_credentials(body)
        try:
            user = db.find_user(conn, creds["username"], creds["password"])
        except Exception:
            app.logger.exception("login query failed")
            return jsonify(error="server error"), 500
        if user is None:
            return jsonify(ok=False), 401
        response = jsonify(ok=True)
        response.set_cookie("token", AUTH_TOKEN, httponly=True)
        return response

    @app.post("/api/logout")
    def logout():
        response = jsonify(ok=True)
        response.delete_cookie("token")
        return response

    @app.get("/api/me")
    @require_auth
    def me():
        return jsonify(username="admin")

    @app.get("/api/widgets")
    @require_auth
    def widgets():
        try:
            return jsonify(db.list_widgets(conn))
        except Exception:
            app.logger.exception("widgets query failed")
            return jsonify(error="server error"), 500

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    return app
