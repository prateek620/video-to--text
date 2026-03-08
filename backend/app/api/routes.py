from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Iterable

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.requests import VideoLinkRequest
from app.schemas.responses import ProcessingStatusResponse, SearchResponse, SearchResultItem, UploadResponse
from app.services.pipeline import VideoInput, VideoProcessingPipeline
from app.services.processing_store import ProcessingStore
from app.services.video_downloader import VideoDownloadDisabledError, VideoDownloadError
from app.services.video_ingestion import ingest_from_link, save_uploads

router = APIRouter()
store = ProcessingStore()
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
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    
    fmt = output_format.lower().strip()
    
    if fmt == "markdown":
        target = settings.documents_dir / f"{job_id}.md"
    elif fmt == "pdf":
        target = settings.documents_dir / f"{job_id}.pdf"
    else:
        target = settings.documents_dir / f"{job_id}.md"
    
    if not Path(target).exists():
        raise HTTPException(status_code=404, detail=f"Document not ready: {target}")
    
    return FileResponse(path=target, filename=Path(target).name)

@router.post("/upload-video", response_model=UploadResponse)
async def upload_video(files: list[UploadFile], background_tasks: BackgroundTasks, merge_videos: bool = False, output_format: str = "markdown") -> UploadResponse:
    job_id = uuid.uuid4().hex
    store.create(job_id)
    store.update(job_id, status="processing", progress=0.01, detail="Job created")
    
    try:
        saved_paths = await save_uploads(files)
    except Exception as exc:
        store.update(job_id, status="failed", progress=1.0, detail=f"Upload failed: {exc}")
        raise HTTPException(status_code=400, detail=f"Failed to save files: {exc}")
    
    background_tasks.add_task(_process_uploaded_videos, job_id, saved_paths, merge_videos, output_format)
    return UploadResponse(job_id=job_id, status="queued", video_count=len(files))

def _process_job(job_id: str, files: list[Path], merge_videos: bool, output_format: str, meta: list = None):
    """Background job to process videos."""
    try:
        store.update(job_id, status="processing", progress=10, detail="Starting video processing...")
        
        pipe = VideoProcessingPipeline()
        items = []
        
        for i, p in enumerate(files):
            progress = 10 + (i * 40 // len(files))
            store.update(job_id, status="processing", progress=progress, detail=f"Processing video {i+1}/{len(files)}...")
            
            vi = VideoInput(
                source_id=f"video-{i+1}",
                path=p,
                source_url=(meta[i].get("source_url") if meta and i < len(meta) else None),
                output_format=output_format
            )
            try:
                item = pipe.process_video(vi)
                items.append(item)
                logger.info(f"Successfully processed video {i+1}")
            except Exception as e:
                logger.exception(f"Error processing video {i+1}: {e}")
                items.append(f"Error: Failed to process video {i+1}")
        
        store.update(job_id, status="processing", progress=60, detail="Building knowledge document...")
        
        result = pipe.build_knowledge(job_id, f"Video {job_id[:8]}", items)
        document_content = result.get("document", "")
        
        store.update(job_id, status="processing", progress=80, detail="Generating documents...")
        
        settings.documents_dir.mkdir(parents=True, exist_ok=True)
        
        # Save markdown
        md_path = settings.documents_dir / f"{job_id}.md"
        md_path.write_text(document_content, encoding="utf-8")
        logger.info(f"Saved markdown: {md_path}")
        
        # Generate PDF
        try:
            pdf_path = settings.documents_dir / f"{job_id}.pdf"
            _markdown_to_pdf(document_content, str(pdf_path))
            logger.info(f"Saved PDF: {pdf_path}")
        except Exception as e:
            logger.warning(f"PDF generation skipped: {e}")
        
        store.update(job_id, status="done", progress=100, detail="Processing complete!")
        logger.info(f"Job {job_id} completed successfully")
        
    except Exception as e:
        logger.exception(f"Job {job_id} failed: {e}")
        store.update(job_id, status="failed", progress=100, detail=f"Error: {str(e)}")

def _markdown_to_pdf(markdown_content: str, pdf_path: str):
    """Convert markdown to PDF."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_JUSTIFY
        
        doc = SimpleDocTemplate(pdf_path, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            textColor='#1a1a1a',
            spaceAfter=20
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )
        
        lines = markdown_content.split('\n')
        for line in lines:
            if line.startswith('# '):
                title = line.replace('# ', '').strip()
                story.append(Paragraph(title, title_style))
                story.append(Spacer(1, 0.2*inch))
            elif line.strip() and not line.startswith('---'):
                story.append(Paragraph(line.strip(), body_style))
        
        doc.build(story)
        
    except ImportError:
        raise Exception("reportlab required: pip install reportlab")

def _ingest_and_process_link_job(job_id: str, request: VideoLinkRequest) -> None:
    try:
        store.update(job_id, status="processing", progress=5, detail="Downloading...")
        _, dl = ingest_from_link(str(request.url))
        if not dl.paths:
            raise RuntimeError("No files downloaded")
        store.update(job_id, status="processing", progress=20, detail=f"Download complete")
        _process_job(job_id, dl.paths, request.merge_videos, request.output_format or "markdown", dl.metadata)
    except Exception as exc:
        logger.exception("Job failed")
        store.update(job_id, status="failed", progress=100, detail=f"Error: {exc}")

def _process_uploaded_videos(job_id: str, saved_paths: list[Path], merge_videos: bool, output_format: str) -> None:
    try:
        store.update(job_id, status="processing", progress=20, detail="Upload complete")
        _process_job(job_id, saved_paths, merge_videos, output_format, None)
    except Exception as exc:
        logger.exception("Job failed")
        store.update(job_id, status="failed", progress=100, detail=f"Error: {exc}")

