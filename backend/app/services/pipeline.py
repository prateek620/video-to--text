from __future__ import annotations

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


@dataclass
class VideoInput:
    source_id: str
    path: Path
    source_url: str | None = None


class VideoProcessingPipeline:
    def process_video(self, video_input: VideoInput) -> VideoKnowledge:
        audio_path = audio_processing.extract_audio(video_input.path)
        transcript = transcribe_audio(str(audio_path))
        frames = frame_analysis.extract_frames(str(video_input.path))
        scenes = frame_analysis.detect_scenes(frames)
        ocr_text = extract_text_from_frames(frames)
        visuals = describe_frames(frames)
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
        combined_transcript_segments = []
        source_url = None
        knowledge_items = list(knowledge_items)
        if not knowledge_items:
            raise RuntimeError("No knowledge artifacts available to build document.")
        for item in knowledge_items:
            combined_transcript_segments.extend(item.transcript.segments)
            combined_transcript_segments.extend(
                [
                    TranscriptSegment(
                        start=frame_text.timestamp,
                        end=frame_text.timestamp,
                        text=f"Visible on screen at {frame_text.timestamp:.0f} seconds: {frame_text.text}",
                    )
                    for frame_text in item.ocr_text
                    if frame_text.text.strip()
                ]
            )
            combined_transcript_segments.extend(
                [
                    TranscriptSegment(
                        start=frame_description.timestamp,
                        end=frame_description.timestamp,
                        text=(
                            f"Visual context at {frame_description.timestamp:.0f} seconds: "
                            f"{frame_description.description}"
                        ),
                    )
                    for frame_description in item.visuals
                    if frame_description.description.strip()
                ]
            )
            source_url = source_url or item.source_url

        combined_transcript_segments.sort(key=lambda segment: segment.start)
        combined_transcript = Transcript(segments=combined_transcript_segments, language="en")

        doc = knowledge_builder.build_document(title, combined_transcript, source_url)
        bundle = generate_documents(doc, job_id)
        index = KnowledgeIndex()
        index.build(doc.chapters)

        return ProcessingResult(
            document_bundle=bundle,
            knowledge_graph=doc.knowledge_graph,
            chapters=doc.chapters,
            timeline_index=doc.timeline_index,
            search_index=index,
        )
