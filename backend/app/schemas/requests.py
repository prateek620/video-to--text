from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class VideoLinkRequest(BaseModel):
    url: HttpUrl = Field(..., description="Video or playlist URL")
    merge_videos: bool = Field(False, description="Merge multiple videos into one knowledge doc")
    output_format: str = Field("markdown", description="Preferred output format")


class SearchRequest(BaseModel):
    job_id: str = Field(..., description="Processing job identifier")
    query: str = Field(..., min_length=1, description="Search query")
    top_k: int = Field(5, ge=1, le=20)
