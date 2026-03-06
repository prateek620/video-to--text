from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.requests import VideoLinkRequest
from app.schemas.responses import ProcessingStatusResponse, SearchResponse, SearchResultItem, UploadResponse
from app.services.pipeline import VideoInput, VideoProcessingPipeline
from app.services.processing_store import ProcessingStore
from app.services.video_ingestion import ingest_from_link, save_uploads


router = APIRouter()
store = ProcessingStore()
pipe = VideoProcessingPipeline()
logger = logging.getLogger(__name__)


@router.get("/")
def root() -> dict[str, str]:
    return {"message": "Video2Knowledge AI backend online"}


@router.post("/upload-video", response_model=UploadResponse)
async def upload_video(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    merge_videos: bool = Query(False),
    output_format: str = Query("markdown"),
) -> UploadResponse:
    job_id, paths = save_uploads(files)
    store.create(job_id, status="queued")
    background_tasks.add_task(_process_job, job_id, paths, merge_videos, output_format)
    return UploadResponse(job_id=job_id, status="queued", video_count=len(paths))


@router.post("/upload-link", response_model=UploadResponse)
async def upload_link(request: VideoLinkRequest, background_tasks: BackgroundTasks) -> UploadResponse:
    try:
        job_id, download_result = ingest_from_link(str(request.url))
    except RuntimeError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    store.create(job_id, status="queued")
    background_tasks.add_task(
        _process_job,
        job_id,
        download_result.paths,
        request.merge_videos,
        request.output_format,
        download_result.metadata,
    )
    return UploadResponse(job_id=job_id, status="queued", video_count=len(download_result.paths))


@router.get("/processing-status", response_model=ProcessingStatusResponse)
def processing_status(job_id: str = Query(...)) -> ProcessingStatusResponse:
    record = store.get(job_id)
    if not record:
        raise HTTPException(status_code=404, detail="Job not found")
    return ProcessingStatusResponse(
        job_id=job_id,
        status=record.status,
        progress=record.progress,
        detail=record.detail,
        output_formats=record.output_formats,
    )


@router.get("/download-document")
def download_document(job_id: str = Query(...), output_format: str = Query("markdown")) -> FileResponse:
    record = store.get(job_id)
    if not record or not record.result:
        raise HTTPException(status_code=404, detail="Document not ready")

    bundle = record.result.document_bundle
    format_lookup = {
        "markdown": bundle.markdown_path,
        "pdf": bundle.pdf_path,
        "docx": bundle.docx_path,
    }
    file_path = format_lookup.get(output_format)
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Requested format not available")

    return FileResponse(path=file_path, filename=file_path.name)


@router.get("/search-knowledge", response_model=SearchResponse)
def search_knowledge(job_id: str = Query(...), query: str = Query(...), top_k: int = Query(5, ge=1, le=20)) -> SearchResponse:
    record = store.get(job_id)
    if not record or not record.result:
        raise HTTPException(status_code=404, detail="Job not ready")

    index = record.result.search_index
    hits = index.search(query, top_k=top_k) if index else []
    results = [
        SearchResultItem(section_title=hit.title, score=hit.score, timestamp=hit.timestamp, snippet=hit.snippet)
        for hit in hits
    ]
    return SearchResponse(job_id=job_id, query=query, results=results)


def _process_job(
    job_id: str,
    paths: Iterable[Path],
    merge_videos: bool,
    output_format: str,
    video_metadata: Iterable | None = None,
) -> None:
    try:
        store.update(job_id, status="processing", progress=0.05, detail="Starting pipeline")
        video_inputs = []
        metadata_items = list(video_metadata) if video_metadata else []
        for index, path in enumerate(paths):
            source_url = metadata_items[index].source_url if index < len(metadata_items) else None
            video_inputs.append(VideoInput(source_id=f"video-{index + 1}", path=Path(path), source_url=source_url))

        if not video_inputs:
            raise RuntimeError("No videos provided for processing.")

        knowledge_items = []
        progress_step = 0.7 / max(len(video_inputs), 1)
        for index, video in enumerate(video_inputs, start=1):
            store.update(job_id, progress=0.1 + progress_step * (index - 1), detail=f"Processing {video.source_id}")
            knowledge_items.append(pipe.process_video(video))

        store.update(job_id, progress=0.85, detail="Building knowledge document")
        default_title = "Video2Knowledge AI Document"
        title = metadata_items[0].title if metadata_items and metadata_items[0].title else default_title
        if merge_videos and len(video_inputs) > 1:
            title = f"Merged Knowledge: {title}"
        items_to_use = knowledge_items if merge_videos else knowledge_items[:1]
        result = pipe.build_knowledge(job_id, title, items_to_use)

        store.set_result(job_id, result, output_formats=["markdown", "pdf", "docx"])
        store.update(job_id, status="completed", progress=1.0, detail="Complete")
    except (RuntimeError, ValueError, OSError) as exc:  # pragma: no cover - defensive guard for background tasks
        logger.exception("Video processing failed for job %s", job_id)
        error_type = type(exc).__name__
        store.update(
            job_id, status="failed", progress=1.0, detail=f"processing_error({error_type}): {exc}"
        )
