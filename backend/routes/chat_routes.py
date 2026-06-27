"""Chat routes — sessions + send message (AI orchestrated)."""

from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from database import get_repo
from auth import get_current_user
from models import ChatSession, ChatMessage, SendMessageIn, Job
from ai.providers import get_orchestrator
from ai.prompts import build_chat_system
from services.job_search import search_jobs_serp
router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions")
async def list_sessions(user: dict = Depends(get_current_user)):
    repo = get_repo()
    sessions = await repo.find_many(
        "chat_sessions",
        {"user_id": user["user_id"]},
        sort=[("created_at", -1)],
        limit=50,
    )
    return sessions


@router.post("/sessions")
async def create_session(user: dict = Depends(get_current_user)):
    repo = get_repo()
    sess = ChatSession(user_id=user["user_id"])
    await repo.insert("chat_sessions", sess.model_dump())
    return sess.model_dump()


@router.get("/sessions/{session_id}/messages")
async def list_messages(session_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    sess = await repo.find_one("chat_sessions", {"id": session_id, "user_id": user["user_id"]})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    msgs = await repo.find_many(
        "chat_messages",
        {"session_id": session_id},
        sort=[("created_at", 1)],
        limit=500,
    )
    return {"session": sess, "messages": msgs}


@router.patch("/messages/{message_id}")
async def edit_message(message_id: str, payload: dict, user: dict = Depends(get_current_user)):
    repo = get_repo()
    msg = await repo.find_one("chat_messages", {"id": message_id})
    if not msg or msg.get("user_id") != user["user_id"]:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.get("role") != "assistant":
        raise HTTPException(status_code=403, detail="Only assistant messages can be edited")
    new_content = payload.get("content")
    if not isinstance(new_content, str) or not new_content.strip():
        raise HTTPException(status_code=400, detail="Content must be a non-empty string")
    await repo.update("chat_messages", {"id": message_id}, {"content": new_content})
    updated = await repo.find_one("chat_messages", {"id": message_id})
    return updated


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    await repo.delete("chat_sessions", {"id": session_id, "user_id": user["user_id"]})
    await repo.delete("chat_messages", {"session_id": session_id})
    return {"ok": True}


def _classify_task(content: str, quick_action: str | None) -> str:
    qa = (quick_action or "").lower()
    mapping = {
        "find_jobs": "job_search",
        "improve_resume": "resume_analysis",
        "increase_ats": "ats_score",
        "interview_questions": "career_guidance",
        "career_roadmap": "career_roadmap",
        "explain_jd": "explain_jd",
        "missing_skills": "missing_skills",
        "learning_resources": "learning_resources",
        "salary_insights": "salary_insights",
        "company_research": "company_research",
        "resume_rewrite": "resume_rewrite",
        "mock_interview": "mock_interview",
        "generate_cover_letter": "cover_letter",
    }
    if qa in mapping:
        return mapping[qa]
    c = content.lower()
    if any(k in c for k in ["find", "search", "show", "job", "role", "opening", "vacanc", "hiring"]):
        return "job_search"
    if "resume" in c and ("rewrite" in c or "rewrit" in c):
        return "resume_rewrite"
    if "ats" in c:
        return "ats_score"
    if "cover letter" in c:
        return "cover_letter"
    if "interview" in c:
        return "career_guidance"
    if "roadmap" in c or "plan" in c:
        return "career_roadmap"
    return "career_guidance"


@router.post("/send")
async def send_message(payload: SendMessageIn, user: dict = Depends(get_current_user)):
    repo = get_repo()
    orch = get_orchestrator()

    # 1. Resolve session
    session_id = payload.session_id
    if not session_id:
        sess = ChatSession(user_id=user["user_id"], title=payload.content[:50])
        await repo.insert("chat_sessions", sess.model_dump())
        session_id = sess.id
    else:
        sess = await repo.find_one(
            "chat_sessions", {"id": session_id, "user_id": user["user_id"]}
        )
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")

    # 2. Build context: resume + job (if any)
    resume = await repo.find_one(
        "resumes", {"user_id": user["user_id"], "is_active": True}
    )
    resume_text = (resume or {}).get("content_text")

    job_context = None
    if payload.job_id:
        job = await repo.find_one("jobs_cache", {"id": payload.job_id})
        if job:
            job_context = job

    # 3. Persist user message
    user_msg = ChatMessage(
        session_id=session_id,
        user_id=user["user_id"],
        role="user",
        content=payload.content,
        kind="text",
        job_id=payload.job_id,
    )
    await repo.insert("chat_messages", user_msg.model_dump())

    # 4. Settings — preferred provider
    settings = await repo.find_one("settings", {"user_id": user["user_id"]}) or {}
    preferred = settings.get("preferred_provider", "auto")
    if preferred == "auto":
        preferred = None

    # 5. Generate AI response (JSON)
    task = _classify_task(payload.content, payload.quick_action)
    system = build_chat_system(resume_text, job_context)
    prompt = payload.content
    if payload.quick_action:
        prompt = f"[quick_action={payload.quick_action}]\n{payload.content}"

    payload_out: dict | None = None

    # Special-case: use SerpAPI for job search so we return real job postings
    if task == "job_search":
        jobs = search_jobs_serp(payload.content)
        cached = []
        for j in jobs[:10]:
            job_obj = Job(
                title=j.get("title", "Untitled Role"),
                company=j.get("company", "Unknown"),
                location=j.get("location", "Remote"),
                salary=j.get("salary"),
                experience=j.get("experience"),
                type=j.get("type", "Full-time"),
                description=j.get("description", ""),
                skills=j.get("skills", []) if isinstance(j.get("skills"), list) else [],
                posted=j.get("posted"),
                apply_url=j.get("apply_url"),
                apply_urls=j.get("apply_urls", []),
                source="serpapi",
            )
            await repo.upsert("jobs_cache", {"id": job_obj.id}, job_obj.model_dump())
            cached.append(job_obj.model_dump())
        payload_out = {"jobs": cached}
        # Log job search
        await repo.insert("job_search_history", {
            "user_id": user["user_id"],
            "query": payload.content,
            "results_count": len(cached),
        })
        # Build a friendly assistant text
        text = f"Found {len(cached)} job(s) for \"{payload.content}\". Open any job to analyze it further."
        kind = "job_cards"
        result = {"provider": "serpapi"}
    else:
        try:
            result = await orch.generate_json(
                system=system,
                prompt=prompt,
                task=task,
                preferred_provider=preferred,
            )
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"AI providers unavailable: {str(e)[:120]}")
        data = result["data"] if isinstance(result["data"], dict) else {}
        kind = data.get("kind", "text")
        text = data.get("text")
        if not text or not isinstance(text, str):
            # Defensive: never leak raw model output. Provide a graceful message.
            text = "I had trouble formulating a response. Could you rephrase that?"
        # 6. If job_cards — persist jobs into jobs_cache for workspace access
        if kind == "job_cards" and isinstance(data.get("jobs"), list):
            cached = []
            for j in data["jobs"][:10]:
                if not isinstance(j, dict):
                    continue
                job_obj = Job(
                    title=j.get("title", "Untitled Role"),
                    company=j.get("company", "Unknown"),
                    location=j.get("location", "Remote"),
                    salary=j.get("salary"),
                    experience=j.get("experience"),
                    type=j.get("type", "Full-time"),
                    description=j.get("description", ""),
                    skills=j.get("skills", []) if isinstance(j.get("skills"), list) else [],
                    posted=j.get("posted"),
                    apply_url=j.get("apply_url"),
                    apply_urls=j.get("apply_urls", []),
                    source="ai",
                )
                await repo.upsert("jobs_cache", {"id": job_obj.id}, job_obj.model_dump())
                cached.append(job_obj.model_dump())
            payload_out = {"jobs": cached}
            # Log job search
            await repo.insert("job_search_history", {
                "user_id": user["user_id"],
                "query": payload.content,
                "results_count": len(cached),
            })
        elif kind == "action_plan" and isinstance(data.get("action_plan"), list):
            payload_out = {"action_plan": data["action_plan"]}

    # 7. Persist AI message
    ai_msg = ChatMessage(
        session_id=session_id,
        user_id=user["user_id"],
        role="assistant",
        content=text,
        kind=kind,
        payload=payload_out,
        job_id=payload.job_id,
    )
    await repo.insert("chat_messages", ai_msg.model_dump())

    # 8. Update session title on first AI message
    msg_count = await repo.count("chat_messages", {"session_id": session_id})
    if msg_count <= 2:
        title = payload.content.strip()[:60] or "New conversation"
        await repo.update("chat_sessions", {"id": session_id}, {"title": title})

    return {
        "session_id": session_id,
        "user_message": user_msg.model_dump(),
        "assistant_message": ai_msg.model_dump(),
        "provider": result["provider"],
        "task": task,
    }
