"""Auth routes — email/password authentication."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, Request, Depends

from database import get_repo
from models import RegisterIn, LoginIn, Profile
from auth import (
    hash_password,
    verify_password,
    create_jwt,
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
