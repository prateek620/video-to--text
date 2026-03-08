from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from app.services import audio_processing, frame_analysis, knowledge_builder, multimodal_fusion
from app.services.document_generator import generate_documents
from app.services.knowledge_index import KnowledgeIndex
from app.services.models import ProcessingResult, Transcript, TranscriptSegment, VideoKnowledge
from app.services.ocr_processing import extract_text_from_frames
from app.services.speech_to_text import transcribe_audio
from app.services.visual_understanding import describe_frames

logger = logging.getLogger(__name__)

@dataclass
class VideoInput:
    source_id: str
    path: Path
    source_url: str | None = None

class VideoProcessingPipeline:
    def process_video(self, video_input: VideoInput) -> VideoKnowledge:
        logger.info("[pipeline] %s: extracting audio", video_input.source_id)
        audio_path = audio_processing.extract_audio(video_input.path)

        logger.info("[pipeline] %s: extracting frames", video_input.source_id)
        frames = frame_analysis.extract_frames(str(video_input.path), fps=0.2)

        logger.info("[pipeline] %s: OCR", video_input.source_id)
        ocr_text = extract_text_from_frames(frames)

        logger.info("[pipeline] %s: visual descriptions", video_input.source_id)
        visuals = describe_frames(frames)

        logger.info("[pipeline] %s: scenes", video_input.source_id)
        scenes = frame_analysis.detect_scenes(frames)

        logger.info("[pipeline] %s: transcription", video_input.source_id)
        transcript = transcribe_audio(str(audio_path))

        fusion_summary = multimodal_fusion.fuse_modalities(transcript, ocr_text, visuals)

        return VideoKnowledge(
            source_id=video_input.source_id,
            source_url=video_input.source_url,
            transcript=transcript,
            ocr_text=ocr_text,
            visuals=visuals,
            scenes=scenes,
            fusion_summary=fusion_summary,
        )

    def build_knowledge(self, job_id: str, title: str, knowledge_items: Iterable[VideoKnowledge]) -> ProcessingResult:
        combined: list[TranscriptSegment] = []
        source_url = None
        items = list(knowledge_items)
        if not items:
            raise RuntimeError("No knowledge artifacts available.")

        for item in items:
            # Only add "spoken" content
            combined.extend(item.transcript.segments)
            source_url = source_url or item.source_url

        combined.sort(key=lambda s: s.start)
        transcript = Transcript(segments=combined, language="en")

        doc = knowledge_builder.build_document(title, transcript, source_url)
        bundle = generate_documents(doc, job_id)

        idx = KnowledgeIndex()
        idx.build(doc.chapters)

        return ProcessingResult(
            document_bundle=bundle,
            knowledge_graph=doc.knowledge_graph,
            chapters=doc.chapters,
            timeline_index=doc.timeline_index,
            search_index=idx,
        )