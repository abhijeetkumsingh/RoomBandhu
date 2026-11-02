from io import BytesIO

from app import Room, RoomImage, Wishlist, db


def test_protected_user_routes_redirect_to_login(client):
    for path in ("/dashboard", "/add_room", "/wishlist", "/profile/edit"):
        response = client.get(path)
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/login")

    response = client.post("/wishlist/toggle/1")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_wishlist_toggle_and_page(client, user_factory, room_factory, login_as):
    user_id = user_factory()
    room_id = room_factory(user_id, title="Wishlisted Room")
    login_as(user_id)

    added = client.post(f"/wishlist/toggle/{room_id}")
    assert added.status_code == 200
    assert added.get_json() == {"saved": True, "count": 1}
    page = client.get("/wishlist")
    assert page.status_code == 200
    assert b"Wishlisted Room" in page.data

    removed = client.post(f"/wishlist/toggle/{room_id}")
    assert removed.get_json() == {"saved": False, "count": 0}
    with client.application.app_context():
        assert Wishlist.query.count() == 0


def test_dashboard_shows_owned_listings(client, user_factory, room_factory, login_as):
    user_id = user_factory(name="Dashboard Student")
    room_factory(user_id, title="Dashboard Room")
    login_as(user_id, "Dashboard Student")

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dashboard Student" in response.data
    assert b"Dashboard Room" in response.data


def test_add_room_saves_uploaded_images(
    client,
    user_factory,
    login_as,
    temporary_uploads,
    test_image_bytes,
):
    user_id = user_factory()
    login_as(user_id)
    uploads = [
        (BytesIO(test_image_bytes), f"room-{index}.png")
        for index in range(4)
    ]
    response = client.post(
        "/add_room",
        data={
            "title": "New Test Listing",
            "rent": "3200",
            "room_type": "Shared",
            "location": "Near Test Campus",
            "area": "Test Road",
            "phone": "5550102",
            "description": "A test-only room.",
            "facilities": ["WiFi", "Study Table"],
            "images": uploads,
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.application.app_context():
        room = Room.query.filter_by(title="New Test Listing").one()
        images = RoomImage.query.filter_by(room_id=room.id).order_by(RoomImage.id).all()
        assert room.rent == 3200
        assert room.user_id == user_id
        assert len(images) == 4
        assert images[0].is_primary is True
        assert all((temporary_uploads / image.filename).is_file() for image in images)


def test_add_room_rejects_too_few_images(client, user_factory, login_as):
    user_id = user_factory()
    login_as(user_id)

    response = client.post(
        "/add_room",
        data={
            "title": "Incomplete Listing",
            "rent": "3200",
            "room_type": "Single",
            "location": "Test Area",
            "phone": "5550102",
            "images": (BytesIO(b"\x89PNG\r\n\x1a\n"), "one.png"),
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert b"Please upload at least 4 valid room photos" in response.data
    with client.application.app_context():
        assert Room.query.filter_by(title="Incomplete Listing").count() == 0


def test_room_delete_route_deletes_only_isolated_test_room(
    client,
    user_factory,
    room_factory,
    login_as,
    temporary_uploads,
    application,
):
    user_id = user_factory()
    room_id = room_factory(user_id, title="Room To Delete")
    filename = "temporary-test-upload.png"
    (temporary_uploads / filename).write_bytes(b"test upload")
    with application.app_context():
        db.session.add(RoomImage(room_id=room_id, filename=filename, is_primary=True))
        db.session.commit()
    login_as(user_id)

    response = client.post(f"/delete_room/{room_id}")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    assert not (temporary_uploads / filename).exists()
    with application.app_context():
        assert db.session.get(Room, room_id) is None
        assert RoomImage.query.filter_by(room_id=room_id).count() == 0


def test_room_edit_route_is_not_implemented(client, user_factory, room_factory):
    user_id = user_factory()
    room_id = room_factory(user_id)

    response = client.get(f"/edit_room/{room_id}")

    assert response.status_code == 404


def test_room_edit_data_persists_in_isolated_sqlalchemy_database(
    application, clean_database, user_factory, room_factory
):
    user_id = user_factory()
    room_id = room_factory(user_id, title="Before Edit")
    with application.app_context():
        room = db.session.get(Room, room_id)
        room.title = "After Edit"
        room.rent = 2800
        db.session.commit()
        db.session.expire_all()
        updated = db.session.get(Room, room_id)
        assert updated.title == "After Edit"
        assert updated.rent == 2800


def test_review_submission_and_duplicate_prevention(
    client, application, user_factory, room_factory, login_as
):
    user_id = user_factory()
    room_id = room_factory(user_id, title="Review Room")
    login_as(user_id)

    response = client.post(
        f"/review/{room_id}",
        data={"stars": "5", "text": "Great room for students."},
    )
    assert response.status_code == 302

    duplicate = client.post(
        f"/review/{room_id}",
        data={"stars": "4", "text": "Second review."},
    )
    assert duplicate.status_code == 302
    with application.app_context():
        from app import Review

        reviews = Review.query.filter_by(room_id=room_id, user_id=user_id).all()
        assert len(reviews) == 1
        assert reviews[0].stars == 5


def test_room_edit_profile_route_updates_only_test_user(
    client, application, user_factory, login_as
):
    user_id = user_factory(name="Before Profile Edit")
    login_as(user_id, "Before Profile Edit")

    response = client.post(
        "/profile/edit",
        data={"name": "After Profile Edit", "phone": "5550199"},
    )

    assert response.status_code == 302
    with application.app_context():
        from app import User

        user = db.session.get(User, user_id)
        assert user.name == "After Profile Edit"
        assert user.phone == "5550199"
