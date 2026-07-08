"""Resume routes — upload PDF/DOCX, paste text, fetch active resume."""

from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException

from ..database import get_repo
from ..auth import get_current_user
from ..models import Resume, ResumePasteIn
from ..services.resume_parser import extract_text

router = APIRouter(prefix="/resume", tags=["resume"])


@router.get("/active")
async def get_active(user: dict = Depends(get_current_user)):
    repo = get_repo()
    resume = await repo.find_one(
        "resumes", {"user_id": user["user_id"], "is_active": True}
    )
    return resume or {}


@router.get("/all")
async def list_all(user: dict = Depends(get_current_user)):
    repo = get_repo()
    return await repo.find_many(
        "resumes", {"user_id": user["user_id"]}, sort=[("created_at", -1)], limit=20
    )


@router.post("/upload")
async def upload(file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    repo = get_repo()
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    text, source = extract_text(file.filename or "", file.content_type or "", data)
    if not text or len(text) < 30:
        raise HTTPException(status_code=400, detail="Could not extract text from file")

    # Deactivate previous resumes
    all_resumes = await repo.find_many("resumes", {"user_id": user["user_id"]}, limit=100)
    for r in all_resumes:
        if r.get("is_active"):
            await repo.update("resumes", {"id": r["id"]}, {"is_active": False})

    resume = Resume(
        user_id=user["user_id"],
        filename=file.filename,
        content_text=text,
        source=source,
        is_active=True,
    )
    await repo.insert("resumes", resume.model_dump())
    return resume.model_dump()


@router.post("/paste")
async def paste(payload: ResumePasteIn, user: dict = Depends(get_current_user)):
    repo = get_repo()
    if len(payload.content_text.strip()) < 30:
        raise HTTPException(status_code=400, detail="Resume text too short")
    all_resumes = await repo.find_many("resumes", {"user_id": user["user_id"]}, limit=100)
    for r in all_resumes:
        if r.get("is_active"):
            await repo.update("resumes", {"id": r["id"]}, {"is_active": False})
    resume = Resume(
        user_id=user["user_id"],
        content_text=payload.content_text.strip(),
        source="paste",
        is_active=True,
    )
    await repo.insert("resumes", resume.model_dump())
    return resume.model_dump()


@router.delete("/{resume_id}")
async def delete_resume(resume_id: str, user: dict = Depends(get_current_user)):
    repo = get_repo()
    await repo.delete("resumes", {"id": resume_id, "user_id": user["user_id"]})
    return {"ok": True}
