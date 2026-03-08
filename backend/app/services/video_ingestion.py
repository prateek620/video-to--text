from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.services.file_utils import ensure_dir, safe_filename
from app.services.video_downloader import DownloadResult, download_from_url

logger = logging.getLogger(__name__)

async def save_uploads(files: list[UploadFile]) -> list[Path]:
    try:
        output_dir = settings.uploads_dir  # Changed from UPLOADS_DIR to uploads_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving uploads to: {output_dir}")
        saved_paths = []
        
        for upload in files:
            if not upload.filename:
                logger.warning("Upload has no filename, skipping")
                continue
            
            unique_id = uuid4().hex[:8]
            safe_name = safe_filename(upload.filename)
            filename = f"{unique_id}_{safe_name}"
            output_path = output_dir / filename
            
            logger.info(f"Saving file: {filename} to {output_path}")
            
            content = await upload.read()
            output_path.write_bytes(content)
            saved_paths.append(output_path)
            logger.info(f"Successfully saved: {output_path}")
        
        return saved_paths
    except Exception as exc:
        logger.exception(f"Error saving uploads: {exc}")
        raise

def ingest_from_link(url: str) -> tuple[str, DownloadResult]:
    ensure_dir(settings.uploads_dir)  # Changed from UPLOADS_DIR to uploads_dir
    job_id = uuid4().hex
    download_result = download_from_url(
        url,
        settings.uploads_dir,  # Changed from UPLOADS_DIR to uploads_dir
        allow_video_downloads=settings.allow_video_downloads,
        cookies_from_browser=settings.cookies_from_browser,
    )
    return job_id, download_result
