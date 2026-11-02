import app as room_app
from app import Room, User, db


def test_admin_routes_are_protected(client):
    for path in ("/admin", "/admin/users", "/admin/rooms"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/admin/login")


def test_admin_login_and_dashboard(client, monkeypatch, six_rooms):
    monkeypatch.setattr(room_app, "ADMIN_EMAIL", "pytest-admin@example.test")
    monkeypatch.setattr(room_app, "ADMIN_PASSWORD", "pytest-admin-password")

    response = client.post(
        "/admin/login",
        data={"email": "pytest-admin@example.test", "password": "pytest-admin-password"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin")
    dashboard = client.get("/admin")
    assert dashboard.status_code == 200
    assert b"Test Room 1" in dashboard.data


def test_admin_toggle_user(client, monkeypatch, user_factory):
    monkeypatch.setattr(room_app, "ADMIN_EMAIL", "pytest-admin@example.test")
    monkeypatch.setattr(room_app, "ADMIN_PASSWORD", "pytest-admin-password")
    user_id = user_factory(email="toggle@example.test")
    with client.session_transaction() as state:
        state["is_admin"] = True

    response = client.post(f"/admin/toggle_user/{user_id}")

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(User, user_id).is_active is False


def test_mocked_google_oauth_callback_creates_test_account(
    client, monkeypatch
):
    class FakeGoogleClient:
        def authorize_redirect(self, redirect_uri):
            return room_app.redirect("https://oauth.example.test/authorize")

        def authorize_access_token(self):
            return {
                "userinfo": {
                    "email": "oauth@example.test",
                    "sub": "oauth-test-id",
                    "name": "OAuth Test",
                    "picture": "https://images.example.test/avatar.png",
                }
            }

    monkeypatch.setattr(room_app, "google", FakeGoogleClient())

    start = client.get("/auth/google")
    assert start.status_code == 302
    assert start.headers["Location"] == "https://oauth.example.test/authorize"
    callback = client.get("/auth/google/callback")
    assert callback.status_code == 302
    with client.application.app_context():
        user = User.query.filter_by(email="oauth@example.test").one()
        assert user.google_id == "oauth-test-id"
        assert user.password is None


def test_admin_delete_room_is_scoped_to_isolated_test_database(
    client, user_factory, room_factory
):
    user_id = user_factory()
    room_id = room_factory(user_id, title="Admin Test Room")
    with client.session_transaction() as state:
        state["is_admin"] = True

    response = client.post(f"/admin/delete_room/{room_id}")

    assert response.status_code == 302
    with client.application.app_context():
        assert db.session.get(Room, room_id) is None
