"""Jobs routes — view single job, save/unsave, AI workspace analysis."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from database import get_repo
from auth import get_current_user
from models import SaveJobIn
from ai.providers import get_orchestrator
from ai.prompts import WORKSPACE_SYSTEM

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/saved")
async def list_saved(user: dict = Depends(get_current_user)):
    repo = get_repo()
    saved = await repo.find_many(
        "saved_jobs",
        {"user_id": user["user_id"]},
        sort=[("created_at", -1)],
        limit=100,
    )
    # Hydrate jobs
    out = []
    for s in saved:
        job = await repo.find_one("jobs_cache", {"id": s["job_id"]})
        if job:
            out.append({**job, "saved_at": s.get("created_at")})
    return out


@router.get("/{job_id}")
async def get_job(job_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    job = await repo.find_one("jobs_cache", {"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    is_saved = await repo.find_one(
        "saved_jobs", {"user_id": user["user_id"], "job_id": job_id}
    )
    return {**job, "is_saved": bool(is_saved)}


@router.post("/{job_id}/save")
async def save_job(job_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    job = await repo.find_one("jobs_cache", {"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    existing = await repo.find_one(
        "saved_jobs", {"user_id": user["user_id"], "job_id": job_id}
    )
    if existing:
        return {"ok": True, "already_saved": True}
    await repo.insert("saved_jobs", {"user_id": user["user_id"], "job_id": job_id})
    return {"ok": True}


@router.delete("/{job_id}/save")
async def unsave_job(job_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    await repo.delete("saved_jobs", {"user_id": user["user_id"], "job_id": job_id})
    return {"ok": True}


@router.get("/{job_id}/analysis")
async def get_or_compute_analysis(job_id: str, user: dict = Depends(get_current_user)):
    """Return cached analysis or compute a fresh one with the AI."""
    repo = get_repo()
    job = await repo.find_one("jobs_cache", {"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Cached?
    cache_key = {"user_id": user["user_id"], "job_id": job_id}
    cached = await repo.find_one("job_analyses", cache_key)
    if cached:
        return cached["analysis"]

    return await _compute(repo, user, job, job_id)


@router.post("/{job_id}/analysis/refresh")
async def refresh_analysis(job_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    job = await repo.find_one("jobs_cache", {"id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await repo.delete("job_analyses", {"user_id": user["user_id"], "job_id": job_id})
    return await _compute(repo, user, job, job_id)


async def _compute(repo, user, job, job_id) -> dict:
    orch = get_orchestrator()
    settings = await repo.find_one("settings", {"user_id": user["user_id"]}) or {}
    preferred = settings.get("preferred_provider", "auto")
    if preferred == "auto":
        preferred = None

    resume = await repo.find_one(
        "resumes", {"user_id": user["user_id"], "is_active": True}
    )
    resume_text = (resume or {}).get("content_text", "")

    prompt = f"""JOB:
Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Experience: {job.get('experience')}
Skills: {', '.join(job.get('skills', []))}
Description: {job.get('description')}

USER'S RESUME:
{resume_text[:5000] if resume_text else '(no resume uploaded)'}"""

    try:
        result = await orch.generate_json(
            system=WORKSPACE_SYSTEM,
            prompt=prompt,
            task="resume_analysis",
            preferred_provider=preferred,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"AI providers unavailable: {str(e)[:120]}")
    analysis = result["data"]
    await repo.upsert(
        "job_analyses",
        {"user_id": user["user_id"], "job_id": job_id},
        {
            "user_id": user["user_id"],
            "job_id": job_id,
            "analysis": analysis,
            "provider": result["provider"],
        },
    )
    return analysis
