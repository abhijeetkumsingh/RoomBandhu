"""
firebase.py — Firebase Admin SDK Initialization
================================================
Single place for all Firebase app initialization.
Uses environment variables — never hardcode credentials.
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage

# ── Singleton guard ───────────────────────────────────────────────
_firebase_app = None
_db           = None
_bucket       = None


def init_firebase():
    """Initialize Firebase app once. Safe to call multiple times."""
    global _firebase_app, _db, _bucket

    if _firebase_app:
        return _firebase_app

    # Build service account credentials from env vars
    # (Render stores them as individual env vars, not a JSON file)
    private_key = os.environ.get('FIREBASE_PRIVATE_KEY', '')
    # Render escapes \n — unescape it
    private_key = private_key.replace('\\n', '\n')

    service_account = {
        "type": "service_account",
        "project_id":                  os.environ.get('FIREBASE_PROJECT_ID', ''),
        "private_key_id":              os.environ.get('FIREBASE_PRIVATE_KEY_ID', ''),
        "private_key":                 private_key,
        "client_email":                os.environ.get('FIREBASE_CLIENT_EMAIL', ''),
        "client_id":                   os.environ.get('FIREBASE_CLIENT_ID', ''),
        "auth_uri":                    "https://accounts.google.com/o/oauth2/auth",
        "token_uri":                   "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url":        os.environ.get('FIREBASE_CLIENT_CERT_URL', ''),
    }

    # Allow loading from a JSON file path (for local dev)
    json_path = os.environ.get('FIREBASE_CREDENTIALS_JSON', '')
    if json_path and os.path.exists(json_path):
        cred = credentials.Certificate(json_path)
    else:
        cred = credentials.Certificate(service_account)

    storage_bucket = os.environ.get('FIREBASE_STORAGE_BUCKET', '')

    _firebase_app = firebase_admin.initialize_app(cred, {
        'storageBucket': storage_bucket
    })

    _db     = firestore.client()
    _bucket = storage.bucket()

    return _firebase_app


def get_db():
    """Return Firestore client. Auto-initializes if needed."""
    global _db
    if _db is None:
        init_firebase()
    return _db


def get_bucket():
    """Return Firebase Storage bucket. Auto-initializes if needed."""
    global _bucket
    if _bucket is None:
        init_firebase()
    return _bucket


def get_auth():
    """Return Firebase Auth module."""
    if not _firebase_app:
        init_firebase()
    return auth


def verify_id_token(id_token: str) -> dict | None:
    """
    Verify a Firebase ID token from the client.
    Returns decoded token dict or None on failure.
    Never trust the frontend — always verify server-side.
    """
    try:
        firebase_auth = get_auth()
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        import logging
        logging.warning(f'Token verification failed: {e}')
        return None