"""File storage: local disk by default, or Supabase Storage when configured.

Local disk is fine for a normal always-on server (the default local-dev / Render setup).
It's wrong for serverless hosts like Vercel, where each request can run in a fresh
environment with no access to files a previous request wrote. Set SUPABASE_URL and
SUPABASE_SERVICE_KEY (see core/config.py) to switch every save()/load() call in the app
over to Supabase Storage instead, with no other code changes required.
"""
import os

import requests

from ..core.config import get_settings


def save(category: str, filename: str, data: bytes) -> str:
    """category: 'images' | 'certificates'. Returns a value to store in the DB and pass
    back into load() later -- a local file path, or a Supabase Storage object key."""
    s = get_settings()
    if s.using_object_storage:
        key = f"{category}/{filename}"
        resp = requests.post(
            f"{s.supabase_url}/storage/v1/object/{s.supabase_bucket}/{key}",
            data=data,
            headers={"Authorization": f"Bearer {s.supabase_service_key}",
                    "x-upsert": "true", "Content-Type": "application/octet-stream"},
            timeout=30,
        )
        resp.raise_for_status()
        return key

    folder = os.path.join(s.data_dir, category)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "wb") as f:
        f.write(data)
    return path


def load(stored_path: str | None) -> bytes | None:
    """Returns the file's bytes, or None if stored_path is empty or not found."""
    if not stored_path:
        return None
    s = get_settings()
    if s.using_object_storage:
        resp = requests.get(
            f"{s.supabase_url}/storage/v1/object/{s.supabase_bucket}/{stored_path}",
            headers={"Authorization": f"Bearer {s.supabase_service_key}"},
            timeout=30,
        )
        return resp.content if resp.status_code == 200 else None

    if os.path.exists(stored_path):
        with open(stored_path, "rb") as f:
            return f.read()
    return None
