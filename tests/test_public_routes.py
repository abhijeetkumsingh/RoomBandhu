from bs4 import BeautifulSoup
import pytest


def room_card_titles(response):
    soup = BeautifulSoup(response.data, "html.parser")
    return [node.get_text(strip=True) for node in soup.select(".room-card .card-title")]


def test_homepage_lists_available_rooms(client, six_rooms):
    response = client.get("/")

    assert response.status_code == 200
    assert room_card_titles(response) == [f"Test Room {i}" for i in range(6, 0, -1)]


@pytest.mark.parametrize("room_id", range(1, 7))
def test_all_six_room_detail_routes(client, six_rooms, room_id):
    response = client.get(f"/room/{room_id}")

    assert response.status_code == 200
    assert f"Test Room {room_id}".encode() in response.data


def test_unknown_room_returns_not_found(client):
    assert client.get("/room/999").status_code == 404


def test_search_matches_title_and_location(client, six_rooms):
    by_title = client.get("/", query_string={"q": "Test Room 3"})
    by_location = client.get("/", query_string={"q": "Test Location 5"})

    assert room_card_titles(by_title) == ["Test Room 3"]
    assert room_card_titles(by_location) == ["Test Room 5"]


@pytest.mark.parametrize(
    ("room_type", "expected"),
    [
        ("Single", ["Test Room 4", "Test Room 1"]),
        ("Shared", ["Test Room 5", "Test Room 2"]),
        ("PG", ["Test Room 6", "Test Room 3"]),
    ],
)
def test_room_type_filters(client, six_rooms, room_type, expected):
    response = client.get("/", query_string={"type": room_type})

    assert room_card_titles(response) == expected


def test_max_price_filter(client, six_rooms):
    response = client.get("/", query_string={"max_price": 3000})

    assert room_card_titles(response) == [
        "Test Room 3",
        "Test Room 2",
        "Test Room 1",
    ]


@pytest.mark.parametrize(
    ("sort", "expected"),
    [
        ("price-asc", [f"Test Room {i}" for i in range(1, 7)]),
        ("price-desc", [f"Test Room {i}" for i in range(6, 0, -1)]),
    ],
)
def test_price_sorting(client, six_rooms, sort, expected):
    response = client.get("/", query_string={"sort": sort})

    assert room_card_titles(response) == expected


def test_rating_sorting(client, application, six_rooms):
    _, room_ids = six_rooms
    with application.app_context():
        from app import Review, db

        db.session.add(Review(room_id=room_ids[0], user_id=six_rooms[0], stars=3, text="Okay"))
        db.session.add(Review(room_id=room_ids[1], user_id=six_rooms[0], stars=5, text="Great"))
        db.session.commit()

    response = client.get("/", query_string={"sort": "rating"})

    assert room_card_titles(response)[:2] == ["Test Room 2", "Test Room 1"]
