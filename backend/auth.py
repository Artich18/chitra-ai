"""Authentication helpers — Supabase JWT."""

from __future__ import annotations

import os

from fastapi import HTTPException, Request, Depends
from supabase import create_client

from .database import get_repo


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_ANON_KEY")
)

supabase = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if SUPABASE_URL and SUPABASE_KEY
    else None
)


async def get_current_user(request: Request) -> dict:
    if not supabase:
        raise HTTPException(
            status_code=500,
            detail="Supabase is not configured",
        )

    auth = request.headers.get("Authorization", "")

    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    token = auth.split(" ", 1)[1]

    try:
        user_response = supabase.auth.get_user(token)
        auth_user = user_response.user

        if not auth_user:
            raise HTTPException(
                status_code=401,
                detail="Invalid token",
            )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid token",
        )

    repo = get_repo()

    profile = await repo.find_one(
        "profiles",
        {
            "email": auth_user.email.lower()
        },
    )

    if not profile:
        raise HTTPException(
            status_code=401,
            detail="Profile not found",
        )

    profile.pop("password_hash", None)

    return profile


CurrentUser = Depends(get_current_user)