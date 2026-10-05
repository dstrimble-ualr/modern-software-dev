# INTEGRATION TESTS
# Scope: the real Flask app, real routes, real decorator, real JSON and cookies,
# and real SQL against an in-memory SQLite database seeded exactly like production.
# Flask's test client sends requests straight to the app without opening a port.
import pytest

from app import create_app

GOOD_LOGIN = {"username": "admin", "password": "password"}


@pytest.fixture
def client():
    # Setup: a fresh app with a fresh, seeded in-memory database for every test.
    app = create_app(db_path=":memory:")
    yield app.test_client()
    # Teardown: runs after the test, even if it failed.
    app.config["DB"].close()


class TestLogin:
    def test_correct_credentials_return_ok_and_set_the_auth_cookie(self, client):
        res = client.post("/api/login", json=GOOD_LOGIN)
        assert res.status_code == 200
        assert res.get_json() == {"ok": True}
        assert res.headers["Set-Cookie"].startswith("token=")

    def test_wrong_credentials_return_401_and_no_cookie(self, client):
        res = client.post("/api/login", json={"username": "admin", "password": "nope"})
        assert res.status_code == 401
        assert res.get_json() == {"ok": False}
        assert "Set-Cookie" not in res.headers


class TestProtectedRoutesWithoutCookie:
    def test_me_returns_401(self, client):
        res = client.get("/api/me")
        assert res.status_code == 401
        assert res.get_json() == {"error": "unauthorized"}

    def test_widgets_returns_401(self, client):
        res = client.get("/api/widgets")
        assert res.status_code == 401
        assert res.get_json() == {"error": "unauthorized"}


class TestSessionLifecycle:
    def test_login_me_widgets_logout_me(self, client):
        # The test client keeps cookies between calls, like a browser would.
        assert client.post("/api/login", json=GOOD_LOGIN).status_code == 200

        me = client.get("/api/me")
        assert me.status_code == 200
        assert me.get_json() == {"username": "admin"}

        widgets = client.get("/api/widgets")
        assert widgets.status_code == 200
        assert len(widgets.get_json()) == 3
        assert widgets.get_json()[0] == {
            "id": 1,
            "name": "Widget A",
            "description": "A basic widget",
            "price": 9.99,
        }

        logout = client.post("/api/logout")
        assert logout.status_code == 200
        assert logout.get_json() == {"ok": True}

        assert client.get("/api/me").status_code == 401


class TestStaticFiles:
    def test_serves_the_app_shell_and_the_front_end_script(self, client):
        root = client.get("/")
        assert root.status_code == 200
        assert b'<div id="root">' in root.data

        script = client.get("/static/js/app.js")
        assert script.status_code == 200
        assert "javascript" in script.headers["Content-Type"]
