from __future__ import annotations

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    job_id: str = Field(..., description="Processing job identifier")
    status: str = Field(..., description="Current processing status")
    video_count: int = Field(..., description="Number of videos ingested")


class ProcessingStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    detail: str | None = None
    output_formats: list[str] = []


class SearchResultItem(BaseModel):
    section_title: str
    score: float
    timestamp: float
    snippet: str


class SearchResponse(BaseModel):
    job_id: str
    query: str
    results: list[SearchResultItem]
