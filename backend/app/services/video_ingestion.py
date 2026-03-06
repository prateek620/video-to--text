from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.services.file_utils import ensure_dir, safe_filename
from app.services.video_downloader import DownloadResult, download_from_url


def save_uploads(files: Iterable[UploadFile]) -> tuple[str, list[Path]]:
    ensure_dir(settings.uploads_dir)
    job_id = uuid4().hex
    paths: list[Path] = []
    for upload in files:
        filename = safe_filename(upload.filename, default_ext=".mp4")
        destination = settings.uploads_dir / filename
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        paths.append(destination)
    return job_id, paths


def ingest_from_link(url: str) -> tuple[str, DownloadResult]:
    ensure_dir(settings.uploads_dir)
    job_id = uuid4().hex
    download_result = download_from_url(
        url, settings.uploads_dir, allow_video_downloads=settings.allow_video_downloads
    )
    return job_id, download_result
