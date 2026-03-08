from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.schemas.requests import VideoLinkRequest
from app.schemas.responses import ProcessingStatusResponse, SearchResponse, SearchResultItem, UploadResponse
from app.services.pipeline import VideoInput, VideoProcessingPipeline
from app.services.processing_store import ProcessingStore
from app.services.video_downloader import VideoDownloadDisabledError, VideoDownloadError
from app.services.video_ingestion import ingest_from_link, save_uploads

router = APIRouter()
store = ProcessingStore()
pipe = VideoProcessingPipeline()
logger = logging.getLogger(__name__)

@router.post("/upload-link", response_model=UploadResponse)
async def upload_link(request: VideoLinkRequest, background_tasks: BackgroundTasks) -> UploadResponse:
    job_id = uuid.uuid4().hex
    store.create(job_id)
    store.update(job_id, status="processing", progress=0.01, detail="Job created")
    background_tasks.add_task(_ingest_and_process_link_job, job_id, request)
    return UploadResponse(job_id=job_id, status="queued", video_count=1)

@router.get("/processing-status", response_model=ProcessingStatusResponse)
def processing_status(job_id: str = Query(...)) -> ProcessingStatusResponse:
    rec = store.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    return ProcessingStatusResponse(
        job_id=job_id,
        status=rec.status,
        progress=rec.progress,
        detail=rec.detail,
        output_formats=rec.output_formats,
    )

@router.get("/download-document")
def download_document(job_id: str = Query(...), output_format: str = Query("markdown")) -> FileResponse:
    rec = store.get(job_id)
    if not rec or not rec.result:
        raise HTTPException(status_code=404, detail="Document not ready")

    bundle = rec.result.document_bundle
    fmt = output_format.lower().strip()
    target = {"markdown": bundle.markdown_path, "docx": bundle.docx_path, "pdf": bundle.pdf_path}.get(fmt)
    if not target or not Path(target).exists():
        raise HTTPException(status_code=404, detail="Requested format not available")
    return FileResponse(path=target, filename=Path(target).name)

def _ingest_and_process_link_job(job_id: str, request: VideoLinkRequest) -> None:
    try:
        store.update(job_id, status="processing", progress=0.05, detail="Downloading video from link")
        _, dl = ingest_from_link(str(request.url))
        if not dl.paths:
            raise RuntimeError("No files downloaded")

        store.update(job_id, status="processing", progress=0.20, detail=f"Download complete ({len(dl.paths)} file(s))")
        _process_job(job_id, dl.paths, bool(request.merge_videos), request.output_format or "markdown", dl.metadata)
    except (VideoDownloadDisabledError, VideoDownloadError, Exception) as exc:
        logger.exception("Job failed")
        store.update(job_id, status="failed", progress=1.0, detail=f"{type(exc).__name__}: {exc}")

def _process_job(job_id: str, paths: Iterable[Path], merge_videos: bool, output_format: str, video_metadata: Iterable | None) -> None:
    try:
        logger.info("[job:%s] started processing", job_id)
        files = [Path(p) for p in paths]
        meta = list(video_metadata) if video_metadata else []
        if not files:
            raise RuntimeError("No video paths")

        inputs = [VideoInput(source_id=f"video-{i+1}", path=p, source_url=(meta[i].source_url if i < len(meta) else None)) for i, p in enumerate(files)]

        store.update(job_id, status="processing", progress=0.30, detail="Processing media")
        items = []
        total = len(inputs)
        for i, vi in enumerate(inputs, start=1):
            p0 = 0.30 + ((i - 1) / total) * 0.50
            p1 = 0.30 + (i / total) * 0.50
            store.update(job_id, progress=p0, detail=f"{vi.source_id}: processing")
            items.append(pipe.process_video(vi))
            store.update(job_id, progress=p1, detail=f"{vi.source_id}: done")

        store.update(job_id, status="processing", progress=0.85, detail="Building document")
        title = meta[0].title if meta and getattr(meta[0], "title", None) else "Video2Knowledge AI Document"
        result = pipe.build_knowledge(job_id, title, items if merge_videos else items[:1])

        out_formats = ["markdown", "docx"]
        if result.document_bundle.pdf_path:
            out_formats.append("pdf")

        logger.info("[job:%s] document generation complete", job_id)
        store.set_result(job_id, result, output_formats=out_formats)
        store.update(job_id, status="completed", progress=1.0, detail="Completed")
        logger.info("[job:%s] COMPLETED", job_id)
    except Exception as exc:
        logger.exception("Process failed")
        store.update(job_id, status="failed", progress=1.0, detail=f"{type(exc).__name__}: {exc}")