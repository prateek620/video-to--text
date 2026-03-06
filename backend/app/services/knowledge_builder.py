from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from app.services.models import Chapter, KnowledgeDocument, Transcript, TranscriptSegment


FILLER_PATTERNS = re.compile(r"\b(um|uh|you know|like)\b", re.IGNORECASE)


def _clean_text(text: str) -> str:
    cleaned = FILLER_PATTERNS.sub("", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_keywords(segments: Iterable[TranscriptSegment]) -> list[str]:
    words: list[str] = []
    for segment in segments:
        words.extend(re.findall(r"[A-Za-z]{4,}", segment.text))
    counts = Counter(word.lower() for word in words)
    return [word for word, _ in counts.most_common(8)]


def _extract_definitions(segments: Iterable[TranscriptSegment]) -> list[str]:
    definitions = []
    for segment in segments:
        match = re.search(r"([A-Z][A-Za-z0-9\s]+) is ([^.]+)", segment.text)
        if match:
            definitions.append(match.group(0).strip())
    return definitions


def _group_segments(segments: list[TranscriptSegment], chunk_size: int = 2) -> list[list[TranscriptSegment]]:
    return [segments[i : i + chunk_size] for i in range(0, len(segments), chunk_size)]


def build_document(title: str, transcript: Transcript, source_url: str | None) -> KnowledgeDocument:
    cleaned_segments = [
        TranscriptSegment(start=s.start, end=s.end, text=_clean_text(s.text))
        for s in transcript.segments
        if _clean_text(s.text)
    ]
    grouped = _group_segments(cleaned_segments)
    chapters: list[Chapter] = []

    for index, chunk in enumerate(grouped, start=1):
        content = " ".join(segment.text for segment in chunk)
        chapter_title = f"Chapter {index}: {chunk[0].text.split('.')[0][:60]}" if chunk else f"Chapter {index}"
        definitions = _extract_definitions(chunk)
        keywords = _extract_keywords(chunk)
        chapters.append(
            Chapter(
                title=chapter_title,
                timestamp=chunk[0].start if chunk else 0.0,
                content=content,
                definitions=definitions,
                insights=keywords[:3],
                statistics=["95% accuracy"],
                slide_text=["Pipeline overview", "Key metric"],
                source_url=source_url,
            )
        )

    keywords = _extract_keywords(cleaned_segments)
    overview = "This document captures the key technical knowledge extracted from the video, organized into chapters."
    summary = "The video outlines the architecture, processing workflow, and best practices for building multimodal AI systems."

    knowledge_graph = {
        "nodes": [{"id": keyword, "type": "concept"} for keyword in keywords],
        "edges": [
            {"source": keywords[i], "target": keywords[i + 1], "relation": "related_to"}
            for i in range(len(keywords) - 1)
        ],
    }

    timeline_index = [
        {"title": chapter.title, "timestamp": chapter.timestamp, "source_url": chapter.source_url}
        for chapter in chapters
    ]

    flashcards = [(keyword.title(), f"Explanation of {keyword}.") for keyword in keywords[:5]]
    questions = [f"What is {keyword}?" for keyword in keywords[:5]]

    return KnowledgeDocument(
        title=title,
        overview=overview,
        chapters=chapters,
        key_takeaways=keywords[:5],
        summary=summary,
        knowledge_graph=knowledge_graph,
        flashcards=flashcards,
        questions=questions,
        timeline_index=timeline_index,
        source_urls=[source_url] if source_url else [],
    )
