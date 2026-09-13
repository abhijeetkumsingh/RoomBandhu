"""
services/room_service.py
=========================
All Firestore operations for the 'rooms' collection.
"""

from firebase import get_db
from datetime import datetime
import uuid


def create_room(owner_uid: str, data: dict, image_urls: list) -> dict:
    """Create a new room document in Firestore."""
    db      = get_db()
    room_id = str(uuid.uuid4())
    now     = datetime.utcnow()

    room = {
        'roomId':       room_id,
        'ownerId':      owner_uid,
        'title':        data.get('title', ''),
        'description':  data.get('description', ''),
        'location':     data.get('location', ''),
        'area':         data.get('area', ''),
        'city':         data.get('city', ''),
        'latitude':     data.get('latitude'),
        'longitude':    data.get('longitude'),
        'rent':         int(data.get('rent', 0)),
        'deposit':      int(data.get('deposit', 0)),
        'roomType':     data.get('room_type', 'Single'),
        'phone':        data.get('phone', ''),
        'amenities':    data.get('amenities', []),
        'images':       image_urls,            # Firebase Storage URLs
        'isAvailable':  True,
        'avgRating':    0.0,
        'reviewCount':  0,
        'createdAt':    now,
        'updatedAt':    now,
    }

    db.collection('rooms').document(room_id).set(room)
    return room


def get_room(room_id: str) -> dict | None:
    """Fetch a single room by ID."""
    try:
        doc = get_db().collection('rooms').document(room_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        return None


def update_room(room_id: str, data: dict) -> bool:
    """Update specific fields of a room."""
    try:
        data['updatedAt'] = datetime.utcnow()
        get_db().collection('rooms').document(room_id).update(data)
        return True
    except Exception:
        return False


def delete_room(room_id: str) -> bool:
    """Delete a room and all its sub-collections."""
    try:
        db  = get_db()
        ref = db.collection('rooms').document(room_id)

        # Delete reviews sub-collection
        for rev in ref.collection('reviews').stream():
            rev.reference.delete()

        ref.delete()
        return True
    except Exception:
        return False


def get_all_rooms(available_only: bool = True) -> list:
    """Get all rooms, optionally filtered to available only."""
    try:
        q = get_db().collection('rooms')
        if available_only:
            q = q.where('isAvailable', '==', True)
        q = q.order_by('createdAt', direction='DESCENDING')
        return [d.to_dict() for d in q.stream()]
    except Exception:
        return []


def get_user_rooms(owner_uid: str) -> list:
    """Get all rooms belonging to a specific user."""
    try:
        docs = (get_db().collection('rooms')
                .where('ownerId', '==', owner_uid)
                .order_by('createdAt', direction='DESCENDING')
                .stream())
        return [d.to_dict() for d in docs]
    except Exception:
        return []


def search_rooms(query: str = '', room_type: str = 'All',
                 max_rent: int = 0, sort: str = 'default') -> list:
    """
    Search and filter rooms.
    Firestore doesn't support full-text search natively,
    so we fetch and filter in Python (fine for small datasets).
    For large scale, use Algolia or Typesense.
    """
    try:
        rooms = get_all_rooms(available_only=True)

        # Filter by type
        if room_type and room_type != 'All':
            rooms = [r for r in rooms if r.get('roomType') == room_type]

        # Filter by max rent
        if max_rent:
            rooms = [r for r in rooms if r.get('rent', 0) <= max_rent]

        # Text search across title, location, area
        if query:
            q = query.lower()
            rooms = [r for r in rooms if
                     q in r.get('title', '').lower() or
                     q in r.get('location', '').lower() or
                     q in r.get('area', '').lower() or
                     q in r.get('description', '').lower()]

        # Sort
        if sort == 'price-asc':
            rooms.sort(key=lambda r: r.get('rent', 0))
        elif sort == 'price-desc':
            rooms.sort(key=lambda r: -r.get('rent', 0))
        elif sort == 'rating':
            rooms.sort(key=lambda r: -r.get('avgRating', 0))
        # else: default = newest first (already ordered by createdAt desc)

        return rooms
    except Exception:
        return []


def toggle_availability(room_id: str, owner_uid: str) -> dict:
    """Toggle room availability. Only owner can do this."""
    try:
        db      = get_db()
        ref     = db.collection('rooms').document(room_id)
        room    = ref.get().to_dict()

        if not room or room.get('ownerId') != owner_uid:
            return {'success': False, 'error': 'Not authorised'}

        new_state = not room.get('isAvailable', True)
        ref.update({'isAvailable': new_state, 'updatedAt': datetime.utcnow()})
        return {'success': True, 'available': new_state}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_nearby_rooms(lat: float, lng: float, limit: int = 10) -> list:
    """Get nearby available rooms using Haversine distance."""
    from math import radians, sin, cos, sqrt, atan2

    def haversine(r):
        R    = 6371
        rlat = r.get('latitude')
        rlng = r.get('longitude')
        if rlat is None or rlng is None:
            return float('inf')
        dlat = radians(rlat - lat)
        dlon = radians(rlng - lng)
        a    = (sin(dlat/2)**2 +
                cos(radians(lat)) * cos(radians(rlat)) * sin(dlon/2)**2)
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    rooms = get_all_rooms(available_only=True)
    rooms = [r for r in rooms if r.get('latitude') and r.get('longitude')]
    rooms_with_dist = [(r, haversine(r)) for r in rooms]
    rooms_with_dist.sort(key=lambda x: x[1])

    result = []
    for room, dist in rooms_with_dist[:limit]:
        room['distanceKm'] = round(dist, 2)
        result.append(room)
    return result