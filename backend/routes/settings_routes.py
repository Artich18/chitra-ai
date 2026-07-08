"""User settings (preferred AI provider, theme, etc.)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..database import get_repo
from ..auth import get_current_user

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsPatch(BaseModel):
    preferred_provider: str | None = None  # 'auto' | 'gemini' | 'openai'
    theme: str | None = None
    notifications: bool | None = None


@router.get("")
async def get_settings(user: dict = Depends(get_current_user)):
    repo = get_repo()
    s = await repo.find_one("settings", {"user_id": user["user_id"]})
    if not s:
        s = {"user_id": user["user_id"], "preferred_provider": "auto", "theme": "dark", "notifications": True}
        await repo.insert("settings", s)
    return s


@router.patch("")
async def update_settings(patch: SettingsPatch, user: dict = Depends(get_current_user)):
    repo = get_repo()
    update = {k: v for k, v in patch.model_dump().items() if v is not None}
    if not update:
        return await get_settings(user)
    return await repo.upsert("settings", {"user_id": user["user_id"]}, {"user_id": user["user_id"], **update})
