from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from app.services.models import Chapter, KnowledgeDocument, Transcript, TranscriptSegment

FILLER = re.compile(r"\b(um|uh|you know|like|basically|actually|literally|so|well)\b", re.IGNORECASE)


def _clean(text: str) -> str:
    text = FILLER.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _is_noise(text: str) -> bool:
    if not text:
        return True
    bad = sum(1 for c in text if not (c.isalnum() or c.isspace() or c in ".,:;!?'-_/()%"))
    return (bad / max(len(text), 1)) > 0.35


def _trim(text: str, n: int) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    return t if len(t) <= n else t[: n - 3].rstrip() + "..."


def _keywords(segs: Iterable[TranscriptSegment], limit: int = 10) -> list[str]:
    words: list[str] = []
    for s in segs:
        words.extend(re.findall(r"[A-Za-z][A-Za-z0-9\-\+]{2,}", s.text))
    cnt = Counter(w.lower() for w in words)
    return [w for w, _ in cnt.most_common(limit)]


def _group(segs: list[TranscriptSegment], size: int = 8) -> list[list[TranscriptSegment]]:
    return [segs[i : i + size] for i in range(0, len(segs), size)]


def build_document(title: str, transcript: Transcript, source_url: str | None) -> KnowledgeDocument:
    cleaned = [
        TranscriptSegment(start=s.start, end=s.end, text=_clean(s.text))
        for s in transcript.segments
        if _clean(s.text) and not _is_noise(_clean(s.text))
    ]

    chapters: list[Chapter] = []
    for i, chunk in enumerate(_group(cleaned, 8), start=1):
        content = " ".join(s.text for s in chunk).strip()
        if not content:
            continue
        head = _trim(re.split(r"[.!?]", chunk[0].text)[0].strip() or f"Chapter {i}", 80)
        chapters.append(
            Chapter(
                title=f"Chapter {i}: {head}",
                timestamp=chunk[0].start,
                content=content,
                examples=[s.text for s in chunk if "example" in s.text.lower()][:4],
                statistics=[s.text for s in chunk if re.search(r"\b\d+(\.\d+)?%|\b\d+\b", s.text)][:4],
                insights=_keywords(chunk, 8),
                source_url=source_url,
            )
        )

    takeaways = _keywords(cleaned, 10) or ["No key takeaways extracted"]

    return KnowledgeDocument(
        title=title,
        overview=_trim(" ".join(s.text for s in cleaned[:6]), 900) if cleaned else "No spoken content was available.",
        chapters=chapters,
        key_takeaways=takeaways,
        summary=_trim(" ".join(c.content for c in chapters[:4]), 1000) if chapters else "No chapter content was extracted.",
        knowledge_graph={"nodes": [{"id": k} for k in takeaways], "edges": []},
        flashcards=[(k.title(), "Explained in context with examples.") for k in takeaways[:6]],
        questions=[f"What does '{k}' mean in this video?" for k in takeaways[:6]],
        timeline_index=[{"timestamp": c.timestamp, "title": c.title, "source_url": c.source_url} for c in chapters],
        source_urls=[source_url] if source_url else [],
    )