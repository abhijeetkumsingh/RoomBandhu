import os
import shutil
import sys
from pathlib import Path

import pytest
from flask_sqlalchemy import SQLAlchemy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

_EXTERNAL_ENV = (
    "FIREBASE_SERVICE_ACCOUNT_JSON",
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
)
_saved_env = {name: os.environ.get(name) for name in (*_EXTERNAL_ENV, "DATABASE_URL")}

for name in _EXTERNAL_ENV:
    os.environ[name] = ""

# app.py otherwise chooses the repository database for non-Postgres URLs.
# Use a deliberately unreachable PostgreSQL URL during import, while blocking
# the app's import-time create_all call. The test SQLite URL is installed before
# any SQLAlchemy engine access.
os.environ["DATABASE_URL"] = "postgresql://test-isolation.invalid/blocked"
_original_create_all = SQLAlchemy.create_all
SQLAlchemy.create_all = lambda self, *args, **kwargs: None
try:
    import app as room_app
finally:
    SQLAlchemy.create_all = _original_create_all
    for name, value in _saved_env.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value

from app import (  # noqa: E402
    OTPToken,
    Review,
    Room,
    RoomImage,
    User,
    Wishlist,
    db,
)


@pytest.fixture(scope="session")
def application(tmp_path_factory):
    test_root = tmp_path_factory.mktemp("roombandhu-test-db")
    database_path = (test_root / "test.sqlite").resolve()
    upload_root = (test_root / "uploads").resolve()
    upload_root.mkdir()

    cached_engines = db._app_engines.get(room_app.app, {})
    for engine in cached_engines.values():
        engine.dispose()
    room_app.app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY="pytest-only-secret",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=str(upload_root),
    )
    room_app.UPLOAD_FOLDER = str(upload_root)
    room_app.app.extensions.pop("sqlalchemy")
    db.init_app(room_app.app)

    with room_app.app.app_context():
        engine_url = db.engine.url
        assert engine_url.get_backend_name() == "sqlite"
        assert Path(engine_url.database).resolve() == database_path
        assert database_path != (PROJECT_ROOT / "roombandhu.db").resolve()
        db.create_all()

    yield room_app.app

    with room_app.app.app_context():
        assert Path(db.engine.url.database).resolve() == database_path
        db.drop_all()
        db.session.remove()
        db.engine.dispose()
    shutil.rmtree(test_root)


@pytest.fixture
def clean_database(application):
    with application.app_context():
        assert Path(db.engine.url.database).resolve() != (
            PROJECT_ROOT / "roombandhu.db"
        ).resolve()
        db.drop_all()
        db.create_all()
    yield
    with application.app_context():
        db.session.remove()
        assert Path(db.engine.url.database).resolve() != (
            PROJECT_ROOT / "roombandhu.db"
        ).resolve()
        db.drop_all()


@pytest.fixture
def client(application, clean_database):
    return application.test_client()


@pytest.fixture
def temporary_uploads(application, tmp_path, monkeypatch):
    upload_root = tmp_path / "uploads"
    upload_root.mkdir()
    monkeypatch.setattr(room_app, "UPLOAD_FOLDER", str(upload_root))
    application.config["UPLOAD_FOLDER"] = str(upload_root)
    yield upload_root
    shutil.rmtree(upload_root)


@pytest.fixture
def user_factory(application):
    def create_user(
        name="Test User",
        email="test@example.test",
        phone=None,
        password="secret123",
        is_active=True,
        google_id=None,
    ):
        with application.app_context():
            from werkzeug.security import generate_password_hash

            user = User(
                name=name,
                email=email,
                phone=phone,
                password=(
                    generate_password_hash(password, method="pbkdf2:sha256")
                    if password is not None
                    else None
                ),
                is_active=is_active,
                google_id=google_id,
            )
            db.session.add(user)
            db.session.commit()
            return user.id

    return create_user


@pytest.fixture
def room_factory(application):
    def create_room(
        user_id,
        title="Test Room",
        rent=2500,
        room_type="Single",
        location="Test Area",
        area="Test Landmark",
        phone="1234567890",
        description="A test room.",
        facilities='["WiFi"]',
        latitude=None,
        longitude=None,
        is_available=True,
    ):
        with application.app_context():
            room = Room(
                title=title,
                rent=rent,
                room_type=room_type,
                location=location,
                area=area,
                phone=phone,
                description=description,
                facilities=facilities,
                latitude=latitude,
                longitude=longitude,
                is_available=is_available,
                user_id=user_id,
            )
            db.session.add(room)
            db.session.commit()
            return room.id

    return create_room


@pytest.fixture
def six_rooms(application, user_factory, room_factory):
    owner_id = user_factory()
    room_ids = []
    for index, (rent, room_type) in enumerate(
        (
            (1000, "Single"),
            (2000, "Shared"),
            (3000, "PG"),
            (4000, "Single"),
            (5000, "Shared"),
            (6000, "PG"),
        ),
        start=1,
    ):
        room_ids.append(
            room_factory(
                owner_id,
                title=f"Test Room {index}",
                rent=rent,
                room_type=room_type,
                location=f"Test Location {index}",
            )
        )
    return owner_id, room_ids


@pytest.fixture
def login_as(client):
    def login(user_id, name="Test User"):
        with client.session_transaction() as state:
            state["user_id"] = user_id
            state["user_name"] = name

    return login


@pytest.fixture
def test_image_bytes():
    from io import BytesIO

    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (4, 4), color=(90, 140, 200)).save(output, format="PNG")
    return output.getvalue()


@pytest.fixture
def external_auth_mocks(monkeypatch):
    calls = []

    def send_email(email, otp):
        calls.append((email, otp))
        return True

    monkeypatch.setattr(room_app, "send_otp_email", send_email)
    monkeypatch.setattr(
        room_app.firebase_auth,
        "verify_id_token",
        lambda token: {
            "email": "firebase@example.test",
            "email_verified": True,
            "name": "Firebase Test",
            "uid": "firebase-test-uid",
        },
    )
    return calls


__all__ = [
    "OTPToken",
    "Review",
    "Room",
    "RoomImage",
    "User",
    "Wishlist",
    "db",
    "room_app",
]
