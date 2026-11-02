"""Safely migrate demo contact fields and seed sample room listings.

Run without arguments for a read-only preview. Pass --apply to migrate the
configured database and add any missing demo records.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from sqlalchemy import inspect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import Room, User, app, db


DEMO_OWNER_EMAIL = "demo-owner@roombandhu.invalid"
DEMO_OWNER_NAME = "RoomBandhu Demo Host"
DEMO_PHONE_PLACEHOLDER = "DEMO-NO-CONTACT"

DEMO_ROOMS = (
    {
        "title": "Affordable Single Room",
        "rent": 3500,
        "room_type": "Single",
        "location": "Near Government Engineering College, Lakhisarai, Bihar",
        "area": "Lakhisarai",
        "description": (
            "Demo listing for preview purposes only. Example single-room "
            "accommodation near Government Engineering College, Lakhisarai."
        ),
        "facilities": ["Study Space", "Water Supply", "Independent Room"],
    },
    {
        "title": "Student Shared Room",
        "rent": 2000,
        "room_type": "Shared",
        "location": "Near Government Engineering College, Lakhisarai, Bihar",
        "area": "Lakhisarai",
        "description": (
            "Demo listing for preview purposes only. Example shared "
            "accommodation for students near the college."
        ),
        "facilities": ["Shared Accommodation", "Study Space", "Water Supply"],
    },
    {
        "title": "Girls PG",
        "rent": 4000,
        "room_type": "PG",
        "location": "Lakhisarai Town, Bihar",
        "area": "Lakhisarai",
        "description": (
            "Demo listing for preview purposes only. Example girls' PG "
            "accommodation near the college."
        ),
        "facilities": ["PG", "Study Space", "Water Supply"],
    },
    {
        "title": "Premium Student Room",
        "rent": 5000,
        "room_type": "Single",
        "location": "Near College Road, Lakhisarai, Bihar",
        "area": "Lakhisarai",
        "description": (
            "Demo listing for preview purposes only. Example premium "
            "student room near the college."
        ),
        "facilities": ["Furnished", "Study Space", "Water Supply"],
    },
    {
        "title": "Room Near College",
        "rent": 3000,
        "room_type": "Single",
        "location": "Near Government Engineering College, Lakhisarai, Bihar",
        "area": "Lakhisarai",
        "description": (
            "Demo listing for preview purposes only. Example student "
            "accommodation close to the college."
        ),
        "facilities": ["Study Space", "Water Supply", "Student Friendly"],
    },
)


def migrate_sqlite_phone_nullable():
    raw_connection = db.engine.raw_connection()
    cursor = raw_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=OFF")
        cursor.execute("BEGIN IMMEDIATE")

        table_row = cursor.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='room'"
        ).fetchone()
        if not table_row or not table_row[0]:
            raise RuntimeError("The room table is missing or has no CREATE TABLE SQL.")

        create_sql = table_row[0]
        create_sql, table_count = re.subn(
            r'(?i)^CREATE TABLE\s+(?:IF NOT EXISTS\s+)?(?:["`\[]?room["`\]]?)\s*\(',
            'CREATE TABLE "room__phone_nullable" (',
            create_sql,
            count=1,
        )
        if table_count != 1:
            raise RuntimeError("Could not safely prepare the room table migration.")

        create_sql, phone_count = re.subn(
            r'(?i)(["`\[]?phone["`\]]?\s+VARCHAR\s*\(\s*15\s*\))\s+NOT\s+NULL\b',
            r"\1",
            create_sql,
            count=1,
        )
        if phone_count != 1:
            raise RuntimeError(
                "The room.phone definition differs from the expected schema; "
                "no migration was applied."
            )

        columns = [
            row[1] for row in cursor.execute('PRAGMA table_info("room")').fetchall()
        ]
        quoted_columns = ", ".join(f'"{name}"' for name in columns)
        original_rows = cursor.execute('SELECT * FROM "room"').fetchall()
        room_indexes = cursor.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE tbl_name='room' AND type IN ('index', 'trigger') "
            "AND sql IS NOT NULL"
        ).fetchall()

        cursor.execute(create_sql)
        cursor.execute(
            f'INSERT INTO "room__phone_nullable" ({quoted_columns}) '
            f'SELECT {quoted_columns} FROM "room"'
        )
        cursor.execute('DROP TABLE "room"')
        cursor.execute(
            'ALTER TABLE "room__phone_nullable" RENAME TO "room"'
        )
        for (statement,) in room_indexes:
            cursor.execute(statement)

        migrated_rows = cursor.execute('SELECT * FROM "room"').fetchall()
        if migrated_rows != original_rows:
            raise RuntimeError("Room rows changed during the SQLite migration.")
        if cursor.execute("PRAGMA foreign_key_check").fetchall():
            raise RuntimeError("Foreign-key validation failed after migration.")

        raw_connection.commit()
    except Exception:
        raw_connection.rollback()
        raise
    finally:
        try:
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()
            raw_connection.close()


def ensure_phone_nullable():
    phone_column = next(
        column
        for column in inspect(db.engine).get_columns("room")
        if column["name"] == "phone"
    )
    if phone_column["nullable"]:
        print("Room.phone is already nullable.")
        return

    if db.engine.dialect.name == "sqlite":
        migrate_sqlite_phone_nullable()
    elif db.engine.dialect.name == "postgresql":
        with db.engine.begin() as connection:
            connection.exec_driver_sql(
                "ALTER TABLE room ALTER COLUMN phone DROP NOT NULL"
            )
    else:
        raise RuntimeError(
            f"Unsupported database backend: {db.engine.dialect.name}"
        )
    print("Room.phone is now nullable; existing room rows were preserved.")


def get_or_create_demo_owner():
    owners = User.query.filter_by(email=DEMO_OWNER_EMAIL).all()
    if len(owners) > 1:
        raise RuntimeError("Multiple reserved demo-owner accounts were found.")
    if owners:
        owner = owners[0]
        if (
            owner.name != DEMO_OWNER_NAME
            or owner.phone is not None
            or owner.password is not None
        ):
            raise RuntimeError(
                "The reserved demo-owner account exists with unexpected data; "
                "it was not changed."
            )
        return owner, False

    owner = User(
        name=DEMO_OWNER_NAME,
        email=DEMO_OWNER_EMAIL,
        phone=None,
        password=None,
    )
    db.session.add(owner)
    db.session.flush()
    return owner, True


def seed_demo_rooms(apply_changes):
    with app.app_context():
        existing_owner = User.query.filter_by(email=DEMO_OWNER_EMAIL).first()
        existing_titles = set()
        if existing_owner:
            existing_titles = {
                room.title for room in Room.query.filter_by(user_id=existing_owner.id)
            }

        missing_rooms = [
            room_data
            for room_data in DEMO_ROOMS
            if room_data["title"] not in existing_titles
        ]
        print(f"Database backend: {db.engine.dialect.name}")
        print(f"Demo owner already exists: {existing_owner is not None}")
        print(f"Demo rooms already present: {len(DEMO_ROOMS) - len(missing_rooms)}")
        print(f"Demo rooms to add: {len(missing_rooms)}")
        print(
            "Demo room phones to update: "
            f"{sum(room.phone is None for room in Room.query.filter_by(user_id=existing_owner.id).all()) if existing_owner else 0}"
        )
        if not apply_changes:
            print("Dry run only. Re-run with --apply to migrate and seed.")
            return

        ensure_phone_nullable()
        try:
            owner, owner_created = get_or_create_demo_owner()
            rooms_by_title = {}
            created_rooms = []
            for room_data in DEMO_ROOMS:
                matches = Room.query.filter_by(
                    user_id=owner.id, title=room_data["title"]
                ).all()
                if len(matches) > 1:
                    raise RuntimeError(
                        f"Duplicate demo room title found: {room_data['title']}"
                    )
                if matches:
                    room = matches[0]
                    expected_facilities = json.dumps(room_data["facilities"])
                    if (
                        room.rent != room_data["rent"]
                        or room.room_type != room_data["room_type"]
                        or room.location != room_data["location"]
                        or room.area != room_data["area"]
                        or room.description != room_data["description"]
                        or room.facilities != expected_facilities
                        or room.phone not in (None, DEMO_PHONE_PLACEHOLDER)
                        or room.is_available is not True
                    ):
                        raise RuntimeError(
                            f"Existing demo room differs from the seed definition: "
                            f"{room_data['title']}. It was not changed."
                        )
                    rooms_by_title[room.title] = room
                    if room.phone is None:
                        room.phone = DEMO_PHONE_PLACEHOLDER
                    continue

                room = Room(
                    title=room_data["title"],
                    rent=room_data["rent"],
                    room_type=room_data["room_type"],
                    location=room_data["location"],
                    area=room_data["area"],
                    description=room_data["description"],
                    phone=DEMO_PHONE_PLACEHOLDER,
                    latitude=None,
                    longitude=None,
                    facilities=json.dumps(room_data["facilities"]),
                    is_available=True,
                    user_id=owner.id,
                )
                db.session.add(room)
                created_rooms.append(room)
                rooms_by_title[room.title] = room

            db.session.flush()
            expected_ids = list(range(2, 7))
            actual_ids = sorted(room.id for room in rooms_by_title.values())
            if actual_ids != expected_ids:
                raise RuntimeError(
                    "Generated room IDs do not match the approved 2–6 image "
                    f"mapping (found: {actual_ids}). No room rows were committed."
                )
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

        print(f"Demo owner created: {owner_created}")
        print(f"Demo rooms created: {len(created_rooms)}")
        for room in created_rooms:
            print(f"  ID {room.id}: {room.title}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="apply the nullable-phone migration and seed missing demo rooms",
    )
    args = parser.parse_args()
    seed_demo_rooms(args.apply)


if __name__ == "__main__":
    main()
