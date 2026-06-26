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

api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"app": "Chitra", "version": "4.0.0", "status": "ok"}


@api_router.get("/health")
async def health():
    repo = get_repo()
    try:
        await repo.db.command("ping")
        return {"status": "ok", "db": "up"}
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
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    repo = get_repo()
    try:
        await repo.db["profiles"].create_index("email", unique=True)
        await repo.db["profiles"].create_index("user_id", unique=True)
        await repo.db["chat_sessions"].create_index("user_id")
        await repo.db["chat_messages"].create_index("session_id")
        await repo.db["saved_jobs"].create_index([("user_id", 1), ("job_id", 1)])
        await repo.db["jobs_cache"].create_index("id", unique=True)
        await repo.db["resumes"].create_index("user_id")
        await repo.db["user_sessions"].create_index("session_token")
        logger.info("Chitra startup complete")
    except Exception as e:
        logger.warning("startup indexes warning: %s", e)


@app.on_event("shutdown")
async def on_shutdown():
    repo = get_repo()
    repo.close()
