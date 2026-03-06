from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Transcript:
    segments: list[TranscriptSegment]
    language: str = "en"


@dataclass
class FrameText:
    timestamp: float
    text: str


@dataclass
class FrameDescription:
    timestamp: float
    description: str


@dataclass
class SceneChange:
    timestamp: float
    label: str


@dataclass
class VideoKnowledge:
    source_id: str
    source_url: str | None
    transcript: Transcript
    ocr_text: list[FrameText]
    visuals: list[FrameDescription]
    scenes: list[SceneChange]
    fusion_summary: str


@dataclass
class Chapter:
    title: str
    timestamp: float
    content: str
    definitions: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    code_snippets: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    statistics: list[str] = field(default_factory=list)
    slide_text: list[str] = field(default_factory=list)
    source_url: str | None = None


@dataclass
class KnowledgeDocument:
    title: str
    overview: str
    chapters: list[Chapter]
    key_takeaways: list[str]
    summary: str
    knowledge_graph: dict[str, Any]
    flashcards: list[tuple[str, str]]
    questions: list[str]
    timeline_index: list[dict[str, Any]]
    source_urls: list[str]


@dataclass
class DocumentBundle:
    markdown_path: Path
    pdf_path: Path | None = None
    docx_path: Path | None = None


@dataclass
class ProcessingResult:
    document_bundle: DocumentBundle
    knowledge_graph: dict[str, Any]
    chapters: list[Chapter]
    timeline_index: list[dict[str, Any]]
    search_index: Any | None = None
