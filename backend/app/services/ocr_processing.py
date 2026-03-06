from __future__ import annotations

from app.services.models import FrameText


SAMPLE_OCR = [
    FrameText(timestamp=60.0, text="Architecture Diagram: ingestion -> processing -> knowledge"),
    FrameText(timestamp=150.0, text="Key Metric: 95% accuracy"),
]


def extract_text_from_frames(_: list[str]) -> list[FrameText]:
    return SAMPLE_OCR
