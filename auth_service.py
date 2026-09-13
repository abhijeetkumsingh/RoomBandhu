"""
services/auth_service.py
========================
All Firebase Authentication operations.
Email/password, Google Sign-In, password reset, email verification.
The Flask backend VERIFIES every token — never trusts frontend claims.
"""

from firebase_admin import auth as fb_auth
from firebase import get_auth, get_db, verify_id_token
from datetime import datetime


def create_email_user(name: str, email: str, password: str, phone: str = '') -> dict:
    """
    Create a new Firebase Auth user with email/password.
    Also creates their Firestore profile document.
    Returns {'success': True, 'uid': ..} or {'success': False, 'error': ..}
    """
    try:
        firebase_auth = get_auth()

        # Create in Firebase Auth
        user_record = firebase_auth.create_user(
            email=email,
            password=password,
            display_name=name,
        )
        uid = user_record.uid

        # Create Firestore profile
        db = get_db()
        db.collection('users').document(uid).set({
            'uid':          uid,
            'name':         name,
            'email':        email,
            'phone':        phone,
            'profileImage': '',
            'role':         'user',
            'isActive':     True,
            'provider':     'email',
            'createdAt':    datetime.utcnow(),
            'updatedAt':    datetime.utcnow(),
        })

        return {'success': True, 'uid': uid}

    except fb_auth.EmailAlreadyExistsError:
        return {'success': False, 'error': 'Email already registered. Please login.'}
    except fb_auth.WeakPasswordError:
        return {'success': False, 'error': 'Password must be at least 6 characters.'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_or_create_google_user(decoded_token: dict) -> dict:
    """
    Called after Google Sign-In on frontend.
    If user exists in Firestore → return profile.
    If new → create Firestore document.
    Returns user profile dict.
    """
    uid    = decoded_token['uid']
    email  = decoded_token.get('email', '')
    name   = decoded_token.get('name', email.split('@')[0])
    avatar = decoded_token.get('picture', '')

    db      = get_db()
    doc_ref = db.collection('users').document(uid)
    doc     = doc_ref.get()

    if doc.exists:
        # Update avatar in case it changed
        doc_ref.update({'profileImage': avatar, 'updatedAt': datetime.utcnow()})
        return doc.to_dict()
    else:
        # First Google login → create profile
        profile = {
            'uid':          uid,
            'name':         name,
            'email':        email,
            'phone':        '',
            'profileImage': avatar,
            'role':         'user',
            'isActive':     True,
            'provider':     'google',
            'createdAt':    datetime.utcnow(),
            'updatedAt':    datetime.utcnow(),
        }
        doc_ref.set(profile)
        return profile


def send_password_reset(email: str) -> dict:
    """
    Generate a Firebase password reset link and (optionally) send it.
    In production: integrate with Flask-Mail or SendGrid.
    Returns {'success': True, 'link': ..} or {'success': False, 'error': ..}
    """
    try:
        firebase_auth = get_auth()
        link = firebase_auth.generate_password_reset_link(email)
        return {'success': True, 'link': link}
    except fb_auth.UserNotFoundError:
        # Don't reveal if email exists (security best practice)
        return {'success': True, 'link': None}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def send_email_verification(uid: str) -> dict:
    """Generate email verification link for a user."""
    try:
        firebase_auth = get_auth()
        user    = firebase_auth.get_user(uid)
        link    = firebase_auth.generate_email_verification_link(user.email)
        return {'success': True, 'link': link}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def revoke_user_tokens(uid: str):
    """Revoke all refresh tokens for a user (force logout everywhere)."""
    try:
        get_auth().revoke_refresh_tokens(uid)
    except Exception:
        pass


def delete_firebase_user(uid: str):
    """Permanently delete a Firebase Auth user."""
    try:
        get_auth().delete_user(uid)
    except Exception:
        pass


def get_firebase_user(uid: str):
    """Get Firebase Auth user record by UID."""
    try:
        return get_auth().get_user(uid)
    except Exception:
        return None