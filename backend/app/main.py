"""FastAPI application factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import REPO_ROOT, get_settings
from app.core.errors import register_exception_handlers
from app.db.session import get_engine
from app.recommendation.runtime import warm_occupation_index

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    with get_engine().connect() as connection:
        connection.execute(text("SELECT 1"))
    try:
        warm_occupation_index()
    except FileNotFoundError:
        pass
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="NSUK Career Guidance API",
        version="0.15.0",
        description=(
            "NSUK career guidance API: questionnaires, assessments, and persisted "
            "O*NET recommendations. Match scores are similarity, not predicted success."
        ),
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    register_exception_handlers(application)
    application.include_router(api_router, prefix="/api/v1")
    _mount_frontend(application)
    return application


def _mount_frontend(application: FastAPI) -> None:
    """Serve the built React app from the same origin as the API.

    Used for a supervisor demo / single-host deploy. Development still uses Vite.
    """
    index = FRONTEND_DIST / "index.html"
    if not index.is_file():
        return
    assets = FRONTEND_DIST / "assets"
    if assets.is_dir():
        application.mount("/assets", StaticFiles(directory=assets), name="frontend-assets")

    @application.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        if full_path.startswith("api/"):
            return FileResponse(index, status_code=404)
        candidate = (FRONTEND_DIST / full_path).resolve()
        try:
            candidate.relative_to(FRONTEND_DIST.resolve())
        except ValueError:
            return FileResponse(index)
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index)


app = create_app()
