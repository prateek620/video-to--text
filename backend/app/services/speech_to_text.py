from __future__ import annotations

from app.services.models import Transcript, TranscriptSegment


SAMPLE_SEGMENTS = [
    TranscriptSegment(start=0.0, end=45.0, text="Introduction to the topic and key objectives."),
    TranscriptSegment(start=45.0, end=120.0, text="Detailed walkthrough of the main concept with examples."),
    TranscriptSegment(start=120.0, end=210.0, text="Discussion of implementation steps and best practices."),
    TranscriptSegment(start=210.0, end=280.0, text="Recap of insights, metrics, and next steps."),
]


def transcribe_audio(_: str) -> Transcript:
    return Transcript(segments=SAMPLE_SEGMENTS, language="en")
