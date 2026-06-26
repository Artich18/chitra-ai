"""
Database Abstraction / Repository Layer
----------------------------------------
All collections behind a simple interface so we can later swap
MongoDB with Supabase (PostgreSQL) without changing business logic.

Logical tables (kept compatible with the future Supabase schema):
- profiles
- chat_sessions
- chat_messages          (chat_history)
- saved_jobs
- jobs_cache
- resumes
- career_roadmaps
- interview_progress
- settings
- user_memories
- job_search_history
- user_sessions          (auth)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from motor.motor_asyncio import AsyncIOMotorClient


class Repository:
    """Thin async repository wrapper around MongoDB collections.

    Every method strips MongoDB's internal `_id` so the public API never
    leaks BSON. All timestamps are ISO strings (UTC) for portability.
    """

    def __init__(self, mongo_url: str, db_name: str):
        self._client = AsyncIOMotorClient(mongo_url)
        self._db = self._client[db_name]

    @property
    def db(self):
        return self._db

    # ---------- generic helpers ----------

    async def find_one(self, table: str, query: dict) -> dict | None:
        return await self._db[table].find_one(query, {"_id": 0})

    async def find_many(
        self,
        table: str,
        query: dict | None = None,
        sort: list | None = None,
        limit: int = 100,
    ) -> list[dict]:
        cursor = self._db[table].find(query or {}, {"_id": 0})
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=limit)

    async def insert(self, table: str, doc: dict) -> dict:
        doc = {**doc}
        doc.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        await self._db[table].insert_one(doc)
        doc.pop("_id", None)
        return doc

    async def update(self, table: str, query: dict, patch: dict) -> dict | None:
        patch = {**patch, "updated_at": datetime.now(timezone.utc).isoformat()}
        await self._db[table].update_one(query, {"$set": patch})
        return await self.find_one(table, query)

    async def upsert(self, table: str, query: dict, patch: dict) -> dict | None:
        patch = {**patch, "updated_at": datetime.now(timezone.utc).isoformat()}
        await self._db[table].update_one(query, {"$set": patch}, upsert=True)
        return await self.find_one(table, query)

    async def delete(self, table: str, query: dict) -> int:
        result = await self._db[table].delete_many(query)
        return result.deleted_count

    async def count(self, table: str, query: dict | None = None) -> int:
        return await self._db[table].count_documents(query or {})

    def close(self):
        self._client.close()


# Lazy singleton
_repo: Repository | None = None


def get_repo() -> Repository:
    global _repo
    if _repo is None:
        _repo = Repository(
            mongo_url=os.environ["MONGO_URL"],
            db_name=os.environ["DB_NAME"],
        )
    return _repo
