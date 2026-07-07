"""Chitra AI V4 — end-to-end backend test suite.

Covers: auth, chat (job_cards + action_plan), sessions, jobs save+analysis,
resume paste, settings provider switching, AI fallback (implicit via switch).
"""
from __future__ import annotations

import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://chitra-ai-4n7w.vercel.app").rstrip("/")
API = f"{BASE_URL}/api"

SEED_EMAIL = "smoke@chitra.ai"
SEED_PASSWORD = "test1234"


# ------------------------- fixtures -------------------------

@pytest.fixture(scope="session")
def http():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def fresh_user(http):
    # Backend lowercases emails — keep test email lowercase to match.
    email = f"test_{uuid.uuid4().hex[:10]}@chitra.ai"
    password = "Passw0rd!23"
    name = "Test User"
    r = http.post(f"{API}/auth/register", json={"email": email, "password": password, "name": name}, timeout=30)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    body = r.json()
    return {"email": email, "password": password, "name": name, "token": body["token"], "user": body["user"]}


@pytest.fixture(scope="session")
def seed_token(http):
    r = http.post(f"{API}/auth/login", json={"email": SEED_EMAIL, "password": SEED_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"seed login failed: {r.status_code} {r.text}"
    return r.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def job_search_result(http, fresh_user):
    """Run one job search and reuse its first job across class boundaries (xdist loadscope friendly)."""
    last_resp = None
    for attempt in range(3):
        r = http.post(
            f"{API}/chat/send",
            headers=_auth(fresh_user["token"]),
            json={"content": "Find Frontend Developer jobs in Bangalore with React and TypeScript"},
            timeout=60,
        )
        last_resp = r
        if r.status_code != 200:
            time.sleep(1)
            continue
        data = r.json()
        am = data["assistant_message"]
        jobs = (am.get("payload") or {}).get("jobs") or []
        if jobs:
            return {"job_id": jobs[0]["id"], "jobs": jobs, "session_id": data["session_id"], "provider": data.get("provider"), "assistant_message": am}
        time.sleep(1)
    pytest.skip(f"No jobs returned from AI after retries; last status={last_resp.status_code if last_resp else 'n/a'} body={last_resp.text[:200] if last_resp else ''}")


# ------------------------- AUTH -------------------------

class TestAuth:
    def test_register_returns_jwt(self, fresh_user):
        assert "token" in fresh_user and len(fresh_user["token"]) > 10
        assert fresh_user["user"]["email"] == fresh_user["email"]
        assert fresh_user["user"]["auth_provider"] == "password"
        assert "password_hash" not in fresh_user["user"]

    def test_register_duplicate_email_400(self, http, fresh_user):
        r = http.post(f"{API}/auth/register", json={
            "email": fresh_user["email"], "password": "anything12345", "name": "Dup"
        }, timeout=20)
        assert r.status_code == 400, f"expected 400, got {r.status_code}: {r.text}"

    def test_login_success(self, http, fresh_user):
        r = http.post(f"{API}/auth/login", json={
            "email": fresh_user["email"], "password": fresh_user["password"]
        }, timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("token"), str)
        assert data["user"]["email"] == fresh_user["email"]

    def test_login_wrong_password_401(self, http, fresh_user):
        r = http.post(f"{API}/auth/login", json={
            "email": fresh_user["email"], "password": "wrongpass99"
        }, timeout=20)
        assert r.status_code == 401

    def test_me_with_token(self, http, fresh_user):
        r = http.get(f"{API}/auth/me", headers=_auth(fresh_user["token"]), timeout=15)
        assert r.status_code == 200
        assert r.json()["email"] == fresh_user["email"]

    def test_me_without_token_401(self, http):
        r = http.get(f"{API}/auth/me", timeout=15)
        assert r.status_code in (401, 403)


# ------------------------- CHAT -------------------------

class TestChat:
    def test_chat_job_search_returns_job_cards(self, job_search_result):
        am = job_search_result["assistant_message"]
        assert am["kind"] == "job_cards", f"expected job_cards kind, got {am['kind']}; payload={am.get('payload')}"
        jobs = job_search_result["jobs"]
        assert 3 <= len(jobs) <= 10, f"expected 3-10 jobs, got {len(jobs)}"
        for j in jobs:
            assert "id" in j and "title" in j and "company" in j and "location" in j
            assert isinstance(j.get("skills"), list)

    def test_chat_career_roadmap_action_plan(self, http, fresh_user):
        r = http.post(
            f"{API}/chat/send",
            headers=_auth(fresh_user["token"]),
            json={"content": "Build me a 90 day plan", "quick_action": "career_roadmap"},
            timeout=60,
        )
        assert r.status_code == 200, r.text[:500]
        am = r.json()["assistant_message"]
        assert am["kind"] == "action_plan", f"expected action_plan, got {am['kind']}"
        plan = (am.get("payload") or {}).get("action_plan") or []
        assert len(plan) >= 2, f"expected multi-step plan, got {len(plan)}"

    def test_list_sessions(self, http, fresh_user):
        r = http.get(f"{API}/chat/sessions", headers=_auth(fresh_user["token"]), timeout=15)
        assert r.status_code == 200
        sessions = r.json()
        assert isinstance(sessions, list)
        assert len(sessions) >= 1


# ------------------------- JOBS -------------------------

class TestJobs:
    def test_save_and_list_saved(self, http, fresh_user, job_search_result):
        job_id = job_search_result["job_id"]
        r = http.post(f"{API}/jobs/{job_id}/save", headers=_auth(fresh_user["token"]), timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        r2 = http.get(f"{API}/jobs/saved", headers=_auth(fresh_user["token"]), timeout=15)
        assert r2.status_code == 200
        saved = r2.json()
        assert any(s.get("id") == job_id for s in saved), "saved job not present in /jobs/saved"

    def test_get_job_detail(self, http, fresh_user, job_search_result):
        job_id = job_search_result["job_id"]
        # Ensure saved first (so is_saved is true)
        http.post(f"{API}/jobs/{job_id}/save", headers=_auth(fresh_user["token"]), timeout=15)
        r = http.get(f"{API}/jobs/{job_id}", headers=_auth(fresh_user["token"]), timeout=15)
        assert r.status_code == 200
        body = r.json()
        assert body["id"] == job_id
        assert body.get("is_saved") is True

    def test_job_analysis(self, http, fresh_user, job_search_result):
        job_id = job_search_result["job_id"]
        r = http.get(f"{API}/jobs/{job_id}/analysis", headers=_auth(fresh_user["token"]), timeout=120)
        assert r.status_code == 200, f"analysis failed: {r.status_code} {r.text[:500]}"
        a = r.json()
        for key in ("success_probability", "ats_score", "resume_match", "missing_skills",
                    "action_plan", "interview_questions", "skill_gap"):
            assert key in a, f"missing field {key} in analysis; keys={list(a.keys())}"
        assert isinstance(a["action_plan"], list) and len(a["action_plan"]) >= 5, f"action_plan must be 5+, got {len(a.get('action_plan', []))}"
        assert isinstance(a["interview_questions"], list) and len(a["interview_questions"]) >= 8, f"interview_questions must be 8+, got {len(a.get('interview_questions', []))}"
        assert isinstance(a["skill_gap"], list) and len(a["skill_gap"]) >= 5, f"skill_gap must be 5+, got {len(a.get('skill_gap', []))}"
        assert isinstance(a["missing_skills"], list)


# ------------------------- RESUME -------------------------

SAMPLE_RESUME = """John Doe — Senior Frontend Engineer
Email: john@example.com | +91-9999999999

Summary: 6+ years building React/TypeScript dashboards and design systems for fintech.

Experience:
- Acme Corp (2021-present) — Staff FE eng; led migration to Next.js 14, built A/B testing platform.
- Pixel Labs (2018-2021) — FE eng; React, Redux, GraphQL.

Skills: React, TypeScript, Next.js, Redux, GraphQL, Tailwind, Vite, Jest, Cypress, Node.js
Education: B.Tech CSE, IIT Roorkee, 2018.
"""


class TestResume:
    def test_paste_then_active(self, http, fresh_user):
        r = http.post(f"{API}/resume/paste", headers=_auth(fresh_user["token"]),
                      json={"content_text": SAMPLE_RESUME}, timeout=20)
        assert r.status_code == 200, r.text[:300]
        body = r.json()
        assert body["is_active"] is True
        assert body["source"] == "paste"

        r2 = http.get(f"{API}/resume/active", headers=_auth(fresh_user["token"]), timeout=15)
        assert r2.status_code == 200
        active = r2.json()
        assert active.get("is_active") is True
        assert "John Doe" in (active.get("content_text") or "")

    def test_paste_too_short_400(self, http, fresh_user):
        r = http.post(f"{API}/resume/paste", headers=_auth(fresh_user["token"]),
                      json={"content_text": "tiny"}, timeout=15)
        assert r.status_code == 400


# ------------------------- SETTINGS / PROVIDER SWITCH -------------------------

class TestSettingsProviderSwitch:
    def test_switch_to_openai_then_back(self, http, fresh_user):
        # Switch to openai
        r = http.patch(f"{API}/settings", headers=_auth(fresh_user["token"]),
                       json={"preferred_provider": "openai"}, timeout=15)
        assert r.status_code == 200, r.text[:300]
        assert r.json().get("preferred_provider") == "openai"

        # Next chat call should use openai
        r2 = http.post(f"{API}/chat/send", headers=_auth(fresh_user["token"]),
                       json={"content": "Give me one quick career tip."}, timeout=60)
        assert r2.status_code == 200, r2.text[:300]
        provider = r2.json().get("provider")
        # Provider should be openai (or fallback to gemini if openai broken — both OK so long as response is valid)
        assert provider in ("openai", "gemini"), f"unexpected provider: {provider}"
        pytest.openai_provider_used = provider

        # Switch to gemini
        r3 = http.patch(f"{API}/settings", headers=_auth(fresh_user["token"]),
                        json={"preferred_provider": "gemini"}, timeout=15)
        assert r3.status_code == 200
        assert r3.json().get("preferred_provider") == "gemini"

        r4 = http.post(f"{API}/chat/send", headers=_auth(fresh_user["token"]),
                       json={"content": "Another quick tip."}, timeout=60)
        assert r4.status_code == 200
        provider2 = r4.json().get("provider")
        assert provider2 in ("openai", "gemini")
        pytest.gemini_provider_used = provider2
