"""Pydantic schemas (kept compatible with Supabase table structures)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field, EmailStr, ConfigDict


def _uuid() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- Auth ----------

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class GoogleSessionIn(BaseModel):
    session_id: str


class Profile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str = Field(default_factory=_uuid)
    email: str
    name: str
    picture: str | None = None
    auth_provider: str = "password"  # 'password' | 'google'
    password_hash: str | None = None
    google_id: str | None = None
    created_at: str = Field(default_factory=_now_iso)


# ---------- Chat ----------

class ChatSession(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    title: str = "New conversation"
    job_id: str | None = None
    created_at: str = Field(default_factory=_now_iso)


class ChatMessage(BaseModel):
    id: str = Field(default_factory=_uuid)
    session_id: str
    user_id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    kind: str = "text"  # 'text' | 'job_cards' | 'action_plan' | 'analysis'
    payload: dict[str, Any] | None = None
    job_id: str | None = None
    created_at: str = Field(default_factory=_now_iso)


class SendMessageIn(BaseModel):
    session_id: str | None = None
    content: str
    quick_action: str | None = None  # e.g. 'find_jobs', 'improve_resume'
    job_id: str | None = None


# ---------- Jobs ----------

class Job(BaseModel):
    id: str = Field(default_factory=_uuid)
    title: str
    company: str
    location: str
    salary: str | None = None
    experience: str | None = None
    type: str = "Full-time"
    description: str = ""
    skills: list[str] = []
    posted: str | None = None
    apply_url: str | None = None
    apply_urls: list[str] = []
    source: str = "ai"  # 'ai' | 'linkedin' | 'jsearch' etc.
    created_at: str = Field(default_factory=_now_iso)


class SaveJobIn(BaseModel):
    job_id: str


class JobSearchIn(BaseModel):
    query: str


# ---------- Resume ----------

class Resume(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    filename: str | None = None
    content_text: str
    source: str = "paste"  # 'paste' | 'pdf' | 'docx'
    is_active: bool = True
    created_at: str = Field(default_factory=_now_iso)


class ResumePasteIn(BaseModel):
    content_text: str


# ---------- Roadmap / Interview / Memory ----------

class CareerRoadmap(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    job_id: str | None = None
    title: str
    steps: list[dict[str, Any]] = []
    created_at: str = Field(default_factory=_now_iso)


class InterviewProgress(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    job_id: str
    question_id: str
    completed: bool = False
    created_at: str = Field(default_factory=_now_iso)


class UserMemory(BaseModel):
    id: str = Field(default_factory=_uuid)
    user_id: str
    key: str
    value: str
    created_at: str = Field(default_factory=_now_iso)


class SettingsModel(BaseModel):
    user_id: str
    preferred_provider: str = "auto"  # 'auto' | 'gemini' | 'openai'
    theme: str = "dark"
    notifications: bool = True
