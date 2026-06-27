"""
Database Abstraction / Repository Layer
----------------------------------------
Supabase (PostgreSQL) implementation — replaces the MongoDB layer.

Logical tables (compatible with Supabase schema):
- profiles
- chat_sessions
- chat_messages
- saved_jobs
- jobs_cache
- resumes
- career_roadmaps
- interview_progress
- settings
- user_memories
- job_search_history
- user_sessions
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from supabase import create_client, Client


class SupabaseRepository:
    """Thin async repository wrapper around Supabase PostgreSQL tables.
    All timestamps are ISO strings (UTC) for portability.
    """

    def __init__(self, url: str, key: str):
        self._client: Client = create_client(url, key)

    # ---------- generic helpers ----------

    async def find_one(self, table: str, query: dict) -> dict | None:
        try:
            filters = []
            for k, v in query.items():
                if k == "id":
                    filters.append(("eq", "id", v))
                elif k == "user_id":
                    filters.append(("eq", "user_id", v))
                elif k == "session_id":
                    filters.append(("eq", "session_id", v))
                elif k == "job_id":
                    filters.append(("eq", "job_id", v))
                elif k == "email":
                    filters.append(("eq", "email", v))
                elif k == "session_token":
                    filters.append(("eq", "session_token", v))
                elif k == "is_active":
                    filters.append(("eq", "is_active", v))
                else:
                    filters.append(("eq", k, v))

            q = self._client.table(table).select("*")
            for op, col, val in filters:
                if op == "eq":
                    q = q.eq(col, val)
            q = q.limit(1)
            resp = q.execute()
            rows = resp.data if resp else []
            return rows[0] if rows else None
        except Exception:
            return None

    async def find_many(
        self,
        table: str,
        query: dict | None = None,
        sort: list | None = None,
        limit: int = 100,
    ) -> list[dict]:
        try:
            q = self._client.table(table).select("*")
            if query:
                for k, v in query.items():
                    if k == "id":
                        q = q.eq("id", v)
                    elif k == "user_id":
                        q = q.eq("user_id", v)
                    elif k == "session_id":
                        q = q.eq("session_id", v)
                    elif k == "job_id":
                        q = q.eq("job_id", v)
                    elif k == "email":
                        q = q.eq("email", v)
                    elif k == "session_token":
                        q = q.eq("session_token", v)
                    elif k == "is_active":
                        q = q.eq("is_active", v)
                    else:
                        q = q.eq(k, v)
            if sort:
                for col, direction in sort:
                    if direction == -1:
                        q = q.order(col, desc=True)
                    else:
                        q = q.order(col)
            q = q.limit(limit)
            resp = q.execute()
            return resp.data if resp else []
        except Exception:
            return []

    async def insert(self, table: str, doc: dict) -> dict:
        doc = {**doc}
        doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        resp = self._client.table(table).insert(doc).execute()
        data = resp.data if resp else []
        return data[0] if data else doc

    async def update(self, table: str, query: dict, patch: dict) -> dict | None:
        patch = {**patch, "updated_at": datetime.now(timezone.utc).isoformat()}
        q = self._client.table(table).update(patch)
        for k, v in query.items():
            if k == "id":
                q = q.eq("id", v)
            elif k == "user_id":
                q = q.eq("user_id", v)
            elif k == "session_id":
                q = q.eq("session_id", v)
            elif k == "job_id":
                q = q.eq("job_id", v)
            elif k == "email":
                q = q.eq("email", v)
            elif k == "session_token":
                q = q.eq("session_token", v)
            else:
                q = q.eq(k, v)
        resp = q.execute()
        data = resp.data if resp else []
        return data[0] if data else None

    async def upsert(self, table: str, query: dict, patch: dict) -> dict | None:
        patch = {**patch, "updated_at": datetime.now(timezone.utc).isoformat()}
        # For upsert: try insert then update, or use Supabase upsert
        try:
            resp = self._client.table(table).upsert(patch).execute()
            data = resp.data if resp else []
            return data[0] if data else None
        except Exception:
            return None

    async def delete(self, table: str, query: dict) -> int:
        q = self._client.table(table).delete()
        for k, v in query.items():
            if k == "id":
                q = q.eq("id", v)
            elif k == "user_id":
                q = q.eq("user_id", v)
            elif k == "session_id":
                q = q.eq("session_id", v)
            elif k == "job_id":
                q = q.eq("job_id", v)
            elif k == "email":
                q = q.eq("email", v)
            elif k == "session_token":
                q = q.eq("session_token", v)
            else:
                q = q.eq(k, v)
        resp = q.execute()
        data = resp.data if resp else []
        return len(data)

    async def count(self, table: str, query: dict | None = None) -> int:
        try:
            q = self._client.table(table).select("*", count="exact", head=True)
            if query:
                for k, v in query.items():
                    if k == "id":
                        q = q.eq("id", v)
                    elif k == "user_id":
                        q = q.eq("user_id", v)
                    elif k == "session_id":
                        q = q.eq("session_id", v)
                    elif k == "job_id":
                        q = q.eq("job_id", v)
                    elif k == "email":
                        q = q.eq("email", v)
                    elif k == "session_token":
                        q = q.eq("session_token", v)
                    elif k == "is_active":
                        q = q.eq("is_active", v)
                    else:
                        q = q.eq(k, v)
            resp = q.execute()
            return resp.count if resp else 0
        except Exception:
            return 0

    def close(self):
        pass


# Lazy singleton
_repo: SupabaseRepository | None = None


def get_repo() -> SupabaseRepository:
    global _repo
    if _repo is None:
        _repo = SupabaseRepository(
            url=os.environ.get("SUPABASE_URL", os.environ.get("VITE_SUPABASE_URL", "")),
            key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", os.environ.get("SUPABASE_ANON_KEY", os.environ.get("VITE_SUPABASE_ANON_KEY", ""))),
        )
    return _repo
