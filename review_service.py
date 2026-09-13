"""
services/review_service.py
===========================
Firestore operations for the 'reviews' sub-collection under each room.
"""

from firebase import get_db
from datetime import datetime


def add_review(room_id: str, uid: str, username: str,
               stars: int, text: str) -> dict:
    """Add a review to a room. Returns result dict."""
    try:
        db      = get_db()
        ref     = db.collection('rooms').document(room_id)

        # Check if already reviewed
        existing = (ref.collection('reviews')
                    .where('userId', '==', uid)
                    .limit(1)
                    .stream())
        for _ in existing:
            return {'success': False, 'error': 'You have already reviewed this room'}

        # Add review
        review_data = {
            'roomId':    room_id,
            'userId':    uid,
            'username':  username,
            'stars':     stars,
            'text':      text,
            'createdAt': datetime.utcnow(),
        }
        ref.collection('reviews').add(review_data)

        # Recalculate avg rating on the room document
        reviews = list(ref.collection('reviews').stream())
        total   = sum(r.to_dict().get('stars', 0) for r in reviews)
        count   = len(reviews)
        avg     = round(total / count, 1) if count else 0.0

        ref.update({
            'avgRating':   avg,
            'reviewCount': count,
            'updatedAt':   datetime.utcnow(),
        })

        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_reviews(room_id: str) -> list:
    """Get all reviews for a room ordered by newest first."""
    try:
        ref  = get_db().collection('rooms').document(room_id)
        docs = (ref.collection('reviews')
                .order_by('createdAt', direction='DESCENDING')
                .stream())
        return [d.to_dict() for d in docs]
    except Exception:
        return []


def has_reviewed(room_id: str, uid: str) -> bool:
    """Check if a user already reviewed a room."""
    try:
        ref = get_db().collection('rooms').document(room_id)
        docs = (ref.collection('reviews')
                .where('userId', '==', uid)
                .limit(1)
                .stream())
        return any(True for _ in docs)
    except Exception:
        return False