from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import ApiKey, ApiKeyEvent, User


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": exp, "iat": datetime.now(timezone.utc)}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def decode_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return int(payload.get("sub"))
    except Exception:
        return None


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    uid = decode_token(token)
    if uid is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    u = db.get(User, uid)
    if u is None or not u.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return u


def optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    uid = decode_token(authorization.split(" ", 1)[1].strip())
    if uid is None:
        return None
    return db.get(User, uid)


def generate_api_key() -> tuple[str, str, str]:
    """Return (full_key, prefix, hash)."""
    raw = secrets.token_urlsafe(32)
    full = f"mni_{raw}"
    prefix = full[:10]
    key_hash = hashlib.sha256(full.encode("utf-8")).hexdigest()
    return full, prefix, key_hash


def verify_api_key_hash(full: str, stored_hash: str) -> bool:
    h = hashlib.sha256(full.encode("utf-8")).hexdigest()
    return hmac.compare_digest(h, stored_hash)


def api_key_user(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    if not x_api_key:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing X-API-Key header")
    prefix = x_api_key[:10]
    rows = db.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.revoked == False)).scalars().all()
    match: ApiKey | None = None
    for row in rows:
        if verify_api_key_hash(x_api_key, row.key_hash):
            match = row
            break
    if match is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    user = db.get(User, match.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found")
    match.last_used_at = datetime.utcnow()
    db.add(match)
    db.add(
        ApiKeyEvent(
            api_key_id=match.id,
            user_id=user.id,
            method=request.method,
            path=request.url.path[:256],
            ip=(request.client.host if request.client else None),
        )
    )
    db.commit()
    return user
