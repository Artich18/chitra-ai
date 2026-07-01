"""Chitra AI — Chat-First Job-Centric Workspace (FastAPI)."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from fastapi import FastAPI, APIRouter  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

from database import get_repo  # noqa: E402
from routes.auth_routes import router as auth_router  # noqa: E402
from routes.chat_routes import router as chat_router  # noqa: E402
from routes.jobs_routes import router as jobs_router  # noqa: E402
from routes.resume_routes import router as resume_router  # noqa: E402
from routes.settings_routes import router as settings_router  # noqa: E402


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("chitra")

app = FastAPI(title="Chitra AI", version="4.0.0")


def _get_allowed_origins() -> list[str]:
    configured = os.environ.get("CORS_ORIGINS", "").strip()
    frontend_url = os.environ.get("FRONTEND_URL", "https://vercel.app").strip()
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]

    if frontend_url and frontend_url not in origins:
        origins.append(frontend_url)
    if "https://www.vercel.app" not in origins:
        origins.append("https://www.vercel.app")
    if not origins:
        origins = ["https://vercel.app", "http://localhost:3000", "http://localhost:5173"]

    return origins


api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"app": "Chitra", "version": "4.0.0", "status": "ok"}


@api_router.get("/health")
async def health():
    repo = get_repo()
    try:
        # Quick connectivity check: count profiles table
        count = await repo.count("profiles")
        return {"status": "ok", "db": "up", "profiles": count}
    except Exception as e:
        return {"status": "degraded", "db": str(e)}


app.include_router(api_router)
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(resume_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=_get_allowed_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    logger.info("Chitra startup complete")


@app.on_event("shutdown")
async def on_shutdown():
    pass
