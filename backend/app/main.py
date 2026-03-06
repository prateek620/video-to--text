from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.services.file_utils import ensure_dir


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.on_event("startup")
    def _startup() -> None:
        ensure_dir(settings.storage_dir)
        ensure_dir(settings.uploads_dir)
        ensure_dir(settings.documents_dir)
        ensure_dir(settings.frames_dir)
        ensure_dir(settings.audio_dir)

    return app


app = create_app()
