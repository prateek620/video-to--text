from __future__ import annotations

from app.services.models import FrameDescription


SAMPLE_DESCRIPTIONS = [
    FrameDescription(timestamp=60.0, description="Slide shows a multi-stage pipeline with ingestion, OCR, and summarization."),
    FrameDescription(timestamp=150.0, description="Chart compares model accuracy across datasets."),
]


def describe_frames(_: list[str]) -> list[FrameDescription]:
    return SAMPLE_DESCRIPTIONS
