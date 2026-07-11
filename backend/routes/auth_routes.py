"""Auth routes — Supabase Auth."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user


@router.post("/login")
async def login():
    return {
        "message": "Login is handled by Supabase Auth on the frontend."
    }


@router.post("/register")
async def register():
    return {
        "message": "Registration is handled by Supabase Auth on the frontend."
    }


@router.post("/logout")
async def logout():
    return {
        "ok": True
    }