from __future__ import annotations

from app.services.models import FrameDescription, FrameText, Transcript


def fuse_modalities(transcript: Transcript, ocr_text: list[FrameText], visuals: list[FrameDescription]) -> str:
    transcript_text = " ".join(segment.text for segment in transcript.segments)
    ocr_section = " ".join(item.text for item in ocr_text)
    visuals_section = " ".join(item.description for item in visuals)
    return "\n".join(
        [
            "Transcript Highlights:",
            transcript_text,
            "OCR Extracts:",
            ocr_section,
            "Visual Descriptions:",
            visuals_section,
        ]
    )
