"""Auth routes — email/password + Emergent Google OAuth."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Response, Request, Depends

from database import get_repo
from models import RegisterIn, LoginIn, GoogleSessionIn, Profile
from auth import (
    hash_password,
    verify_password,
    create_jwt,
    fetch_google_session,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(payload: RegisterIn):
    repo = get_repo()
    existing = await repo.find_one("profiles", {"email": payload.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    profile = Profile(
        email=payload.email.lower(),
        name=payload.name,
        auth_provider="password",
        password_hash=hash_password(payload.password),
    )
    doc = profile.model_dump()
    await repo.insert("profiles", doc)
    await repo.insert("settings", {"user_id": profile.user_id, "preferred_provider": "auto", "theme": "dark"})

    token = create_jwt(profile.user_id)
    safe = {k: v for k, v in doc.items() if k != "password_hash"}
    return {"token": token, "user": safe}


@router.post("/login")
async def login(payload: LoginIn):
    repo = get_repo()
    user = await repo.find_one("profiles", {"email": payload.email.lower()})
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_jwt(user["user_id"])
    user.pop("password_hash", None)
    return {"token": token, "user": user}


@router.post("/google/session")
async def google_session(payload: GoogleSessionIn, response: Response):
    """Exchange Emergent OAuth session_id for our session/cookie."""
    data = await fetch_google_session(payload.session_id)
    repo = get_repo()

    # Upsert profile by email
    existing = await repo.find_one("profiles", {"email": data["email"].lower()})
    if existing:
        user_id = existing["user_id"]
        await repo.update("profiles", {"user_id": user_id}, {
            "name": data.get("name") or existing.get("name"),
            "picture": data.get("picture") or existing.get("picture"),
            "google_id": data.get("id"),
            "auth_provider": existing.get("auth_provider", "google"),
        })
    else:
        profile = Profile(
            email=data["email"].lower(),
            name=data.get("name") or data["email"].split("@")[0],
            picture=data.get("picture"),
            auth_provider="google",
            google_id=data.get("id"),
        )
        await repo.insert("profiles", profile.model_dump())
        await repo.insert("settings", {"user_id": profile.user_id, "preferred_provider": "auto", "theme": "dark"})
        user_id = profile.user_id

    # Store session_token
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    await repo.insert("user_sessions", {
        "user_id": user_id,
        "session_token": data["session_token"],
        "expires_at": expires_at.isoformat(),
    })

    # HttpOnly cookie
    response.set_cookie(
        key="session_token",
        value=data["session_token"],
        path="/",
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        secure=True,
        samesite="none",
    )

    user = await repo.find_one("profiles", {"user_id": user_id})
    if user:
        user.pop("password_hash", None)
    return {"user": user, "session_token": data["session_token"]}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/logout")
async def logout(request: Request, response: Response):
    repo = get_repo()
    cookie_token = request.cookies.get("session_token")
    if cookie_token:
        await repo.delete("user_sessions", {"session_token": cookie_token})
    response.delete_cookie("session_token", path="/")
    return {"ok": True}
