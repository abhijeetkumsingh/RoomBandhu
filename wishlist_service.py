"""
services/wishlist_service.py
==============================
Firestore wishlist operations.
Each user has one 'wishlist' document with a 'roomIds' array.
"""

from datetime import datetime

from firebase import get_db

try:
    from firebase_admin.firestore import ArrayUnion, ArrayRemove
except ImportError:
    try:
        from google.cloud.firestore import ArrayUnion, ArrayRemove
    except ImportError:
        from google.cloud.firestore_v1 import ArrayUnion, ArrayRemove  # type: ignore

try:
    from room_service import get_room
except ImportError:
    from services.room_service import get_room  # type: ignore


def toggle_wishlist(uid: str, room_id: str) -> dict:
    """
    Add or remove a room from user wishlist.
    Returns {'saved': True/False, 'count': N}
    """
    try:
        db  = get_db()
        ref = db.collection('wishlist').document(uid)
        doc = ref.get()

        room_ids = doc.to_dict().get('roomIds', []) if doc.exists else []

        if room_id in room_ids:
            ref.update({'roomIds': ArrayRemove([room_id]),
                        'updatedAt': datetime.utcnow()})
            return {'saved': False, 'count': max(0, len(room_ids) - 1)}
        else:
            if doc.exists:
                ref.update({'roomIds': ArrayUnion([room_id]),
                            'updatedAt': datetime.utcnow()})
            else:
                ref.set({'uid': uid, 'roomIds': [room_id],
                         'updatedAt': datetime.utcnow()})
            return {'saved': True, 'count': len(room_ids) + 1}

    except Exception as e:
        import logging
        logging.error(f'Wishlist error: {e}')
        return {'saved': False, 'count': 0}


def get_wishlist(uid: str) -> list:
    """Get list of room IDs in a user's wishlist."""
    try:
        doc = get_db().collection('wishlist').document(uid).get()
        return doc.to_dict().get('roomIds', []) if doc.exists else []
    except Exception:
        return []


def get_wishlist_count(uid: str) -> int:
    return len(get_wishlist(uid))


def get_wishlisted_rooms(uid: str) -> list:
    return [r for rid in get_wishlist(uid) if (r := get_room(rid))]