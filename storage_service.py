"""
services/storage_service.py
============================
All Firebase Storage operations for room images.
Images are uploaded to Storage; URLs are stored in Firestore.
"""

import os
import uuid
from firebase import get_bucket

ALLOWED_CONTENT_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
MAGIC_BYTES = (
    b'\xff\xd8\xff',   # JPEG
    b'\x89PNG',         # PNG
    b'RIFF',            # WebP
)


def _is_safe_image(file_storage) -> bool:
    """Magic-byte check — not just extension."""
    header = file_storage.read(8)
    file_storage.seek(0)
    return any(header[:len(m)] == m for m in MAGIC_BYTES)


def _allowed_type(file_storage) -> bool:
    return file_storage.content_type in ALLOWED_CONTENT_TYPES


def upload_room_image(file_storage, room_id: str, index: int) -> str | None:
    """
    Upload a single room image to Firebase Storage.
    Returns the public download URL or None on failure.
    """
    try:
        if not _allowed_type(file_storage) or not _is_safe_image(file_storage):
            return None

        ext      = file_storage.filename.rsplit('.', 1)[-1].lower()
        filename = f"rooms/{room_id}/{uuid.uuid4().hex}_{index}.{ext}"

        bucket = get_bucket()
        blob   = bucket.blob(filename)
        blob.upload_from_file(
            file_storage,
            content_type=file_storage.content_type
        )
        blob.make_public()
        return blob.public_url

    except Exception as e:
        import logging
        logging.error(f'Storage upload error: {e}')
        return None


def upload_profile_image(file_storage, uid: str) -> str | None:
    """
    Upload a profile picture to Firebase Storage.
    Returns the public download URL or None on failure.
    """
    try:
        if not _allowed_type(file_storage) or not _is_safe_image(file_storage):
            return None

        ext      = file_storage.filename.rsplit('.', 1)[-1].lower()
        filename = f"profiles/{uid}/avatar.{ext}"

        bucket = get_bucket()
        blob   = bucket.blob(filename)
        blob.upload_from_file(
            file_storage,
            content_type=file_storage.content_type
        )
        blob.make_public()
        return blob.public_url

    except Exception as e:
        import logging
        logging.error(f'Profile image upload error: {e}')
        return None


def delete_image(public_url: str) -> bool:
    """Delete an image from Storage by its public URL."""
    try:
        bucket       = get_bucket()
        # Extract path from URL: .../o/rooms%2F...  or /rooms/...
        if '/o/' in public_url:
            path = public_url.split('/o/')[1].split('?')[0]
            from urllib.parse import unquote
            path = unquote(path)
        else:
            # direct public URL: https://storage.googleapis.com/BUCKET/PATH
            parts = public_url.split(bucket.name + '/')
            path  = parts[1] if len(parts) > 1 else ''

        if path:
            blob = bucket.blob(path)
            blob.delete()
        return True
    except Exception:
        return False


def upload_multiple_images(files: list, room_id: str) -> list:
    """
    Upload a list of FileStorage objects for a room.
    Returns list of public URLs (skips failed uploads).
    """
    urls = []
    for i, f in enumerate(files):
        if f and f.filename:
            url = upload_room_image(f, room_id, i)
            if url:
                urls.append(url)
    return urls