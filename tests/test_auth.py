from app import OTPToken, User, db


def test_registration_creates_user_and_logs_in(client):
    response = client.post(
        "/register",
        data={
            "name": "New Student",
            "email": "NEW@EXAMPLE.TEST",
            "phone": "5550100",
            "password": "secure123",
            "confirm_password": "secure123",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.application.app_context():
        user = User.query.filter_by(email="new@example.test").one()
        assert user.name == "New Student"
        assert user.phone == "5550100"
        assert user.password != "secure123"
    with client.session_transaction() as state:
        assert state["user_name"] == "New Student"


def test_duplicate_registration_redirects_to_login(client, user_factory):
    user_factory(email="duplicate@example.test")

    response = client.post(
        "/register",
        data={
            "name": "Duplicate",
            "email": "DUPLICATE@example.test",
            "password": "secure123",
            "confirm_password": "secure123",
        },
        follow_redirects=True,
    )

    assert response.request.path == "/login"
    assert b"Email already registered" in response.data
    with client.application.app_context():
        assert User.query.filter_by(email="duplicate@example.test").count() == 1


def test_login_rejects_invalid_password(client, user_factory):
    user_factory(email="login@example.test", password="correct123")

    response = client.post(
        "/login",
        data={"email": "login@example.test", "password": "wrong123"},
        follow_redirects=True,
    )

    assert response.request.path == "/login"
    assert b"Incorrect password" in response.data
    with client.session_transaction() as state:
        assert "user_id" not in state


def test_login_and_logout(client, user_factory):
    user_id = user_factory(name="Returning Student", email="return@example.test")
    response = client.post(
        "/login",
        data={"email": "RETURN@example.test", "password": "secret123"},
    )

    assert response.status_code == 302
    with client.session_transaction() as state:
        assert state["user_id"] == user_id
        assert state["user_name"] == "Returning Student"

    response = client.get("/logout")
    assert response.status_code == 302
    with client.session_transaction() as state:
        assert "user_id" not in state
        assert "user_name" not in state


def test_google_only_user_cannot_use_password_login(client, user_factory):
    user_factory(
        email="google@example.test",
        password=None,
        google_id="google-id",
    )

    response = client.post(
        "/login",
        data={"email": "google@example.test", "password": "anything"},
        follow_redirects=True,
    )

    assert response.request.path == "/login"
    assert b"uses Google Sign-In" in response.data


def test_forgot_password_uses_mocked_email(client, user_factory, external_auth_mocks):
    user_factory(email="otp@example.test")

    response = client.post(
        "/forgot-password",
        data={"email": "otp@example.test"},
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/verify-otp")
    assert len(external_auth_mocks) == 1
    assert external_auth_mocks[0][0] == "otp@example.test"
    with client.application.app_context():
        token = OTPToken.query.filter_by(email="otp@example.test").one()
        assert token.otp == external_auth_mocks[0][1]
        assert token.used is False


def test_firebase_login_uses_mocked_token_verification(
    client, external_auth_mocks
):
    response = client.post(
        "/auth/firebase/session",
        json={"idToken": "mock-token"},
    )

    assert response.status_code == 200
    assert response.get_json()["success"] is True
    with client.application.app_context():
        assert User.query.filter_by(email="firebase@example.test").one().name == "Firebase Test"
    with client.session_transaction() as state:
        assert state["user_name"] == "Firebase Test"


def test_google_oauth_routes_are_safe_when_unconfigured(client):
    response = client.get("/auth/google")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
