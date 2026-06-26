"""Authentication helpers — JWT (email+password) + Emergent Google session."""

from __future__ import annotations

import os
import uuid
import bcrypt
import jwt
import requests
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request, Depends

from database import get_repo


JWT_SECRET = os.environ.get("JWT_SECRET", "chitra_dev_secret")
JWT_ALG = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_DAYS = int(os.environ.get("JWT_EXPIRY_DAYS", "7"))

EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_jwt(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_jwt(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except jwt.PyJWTError:
        return None


async def fetch_google_session(session_id: str) -> dict:
    """Exchange session_id with Emergent Auth for user data."""
    resp = requests.get(
        EMERGENT_AUTH_URL,
        headers={"X-Session-ID": session_id},
        timeout=15,
    )
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google session")
    return resp.json()


async def get_current_user(request: Request) -> dict:
    """Resolve current user from either:
       - JWT bearer token (email+password auth)
       - Emergent session_token cookie or bearer (Google auth)
    """
    repo = get_repo()
    auth_header = request.headers.get("Authorization", "")
    token = None
    source = None

    if auth_header.lower().startswith("bearer "):
        token = auth_header.split(" ", 1)[1].strip()

    # 1) Try JWT
    if token:
        payload = decode_jwt(token)
        if payload and payload.get("sub"):
            user = await repo.find_one("profiles", {"user_id": payload["sub"]})
            if user:
                user.pop("password_hash", None)
                return user
        # Not a JWT — maybe it's an Emergent session token
        source = "google_bearer"

    # 2) Try Emergent session_token cookie
    cookie_token = request.cookies.get("session_token")
    candidate = cookie_token or (token if source == "google_bearer" else None)
    if candidate:
        sess = await repo.find_one("user_sessions", {"session_token": candidate})
        if sess:
            expires_at = sess.get("expires_at")
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if not expires_at or expires_at > datetime.now(timezone.utc):
                user = await repo.find_one("profiles", {"user_id": sess["user_id"]})
                if user:
                    user.pop("password_hash", None)
                    return user

    raise HTTPException(status_code=401, detail="Not authenticated")


CurrentUser = Depends(get_current_user)
