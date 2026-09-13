"""
services/user_service.py
=========================
All Firestore operations for the 'users' collection.
"""

from firebase import get_db
from datetime import datetime


def get_user(uid: str) -> dict | None:
    """Fetch user profile from Firestore by UID."""
    try:
        doc = get_db().collection('users').document(uid).get()
        return doc.to_dict() if doc.exists else None
    except Exception:
        return None


def create_user(uid: str, data: dict) -> dict:
    """Create a user document in Firestore."""
    now = datetime.utcnow()
    profile = {
        'uid':          uid,
        'name':         data.get('name', ''),
        'email':        data.get('email', ''),
        'phone':        data.get('phone', ''),
        'profileImage': data.get('profileImage', ''),
        'role':         data.get('role', 'user'),
        'isActive':     True,
        'provider':     data.get('provider', 'email'),
        'createdAt':    now,
        'updatedAt':    now,
    }
    get_db().collection('users').document(uid).set(profile)
    return profile


def update_user(uid: str, data: dict) -> bool:
    """Update specific fields of a user document."""
    try:
        data['updatedAt'] = datetime.utcnow()
        get_db().collection('users').document(uid).update(data)
        return True
    except Exception:
        return False


def get_all_users() -> list:
    """Admin: get all users ordered by creation date."""
    try:
        docs = (get_db().collection('users')
                .order_by('createdAt', direction='DESCENDING')
                .stream())
        return [d.to_dict() for d in docs]
    except Exception:
        return []


def toggle_user_active(uid: str) -> bool:
    """Admin: toggle isActive flag. Returns new state."""
    try:
        db      = get_db()
        doc_ref = db.collection('users').document(uid)
        user    = doc_ref.get().to_dict()
        new_state = not user.get('isActive', True)
        doc_ref.update({'isActive': new_state, 'updatedAt': datetime.utcnow()})
        return new_state
    except Exception:
        return False


def get_user_by_email(email: str) -> dict | None:
    """Find a user document by email."""
    try:
        docs = (get_db().collection('users')
                .where('email', '==', email.lower())
                .limit(1)
                .stream())
        for doc in docs:
            return doc.to_dict()
        return None
    except Exception:
        return None