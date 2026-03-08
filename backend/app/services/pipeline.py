from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services import audio_processing, frame_analysis, knowledge_builder, multimodal_fusion, speech_to_text

logger = logging.getLogger(__name__)

@dataclass
class VideoInput:
    """Input data for video processing pipeline."""
    source_id: str
    path: Path | str
    source_url: str | None = None
    output_format: str = "markdown"
    merge_videos: bool = False

class VideoProcessingPipeline:
    def process(self, video_input: VideoInput) -> str:
        """Process video and generate study document."""
        video_path = Path(video_input.path) if isinstance(video_input.path, str) else video_input.path
        
        logger.info(f"Processing: {video_path}")
        
        try:
            # Extract audio
            logger.info("Extracting audio...")
            audio_path = audio_processing.extract_audio(video_path)
            
            # Transcribe
            logger.info("Transcribing audio...")
            transcript = speech_to_text.transcribe(str(audio_path))
            logger.info(f"Transcript length: {len(transcript)} chars")
            
            # Extract frames (optional)
            logger.info("Extracting frames...")
            try:
                frames = frame_analysis.extract_frames(str(video_path))
                logger.info(f"Extracted {len(frames) if frames else 0} frames")
            except Exception as e:
                logger.warning(f"Frame extraction failed: {e}")
                frames = []
            
            # Detect scenes
            frame_insights = []
            if frames:
                try:
                    logger.info("Detecting scenes...")
                    scenes = frame_analysis.detect_scenes(frames)
                    frame_insights = [{"description": s.label, "timestamp": s.timestamp} for s in scenes] if scenes else []
                    logger.info(f"Detected {len(frame_insights)} scenes")
                except Exception as e:
                    logger.warning(f"Scene detection failed: {e}")
            
            # Fuse data
            logger.info("Fusing audio and visual data...")
            fused_knowledge = multimodal_fusion.fuse(
                transcript=transcript,
                frame_insights=frame_insights,
                video_path=str(video_path)
            )
            
            # Build document
            logger.info("Building study document...")
            document = knowledge_builder.build(fused_knowledge, video_input.output_format)
            logger.info(f"Document generated: {len(document)} chars")
            
            return document
            
        except Exception as exc:
            logger.exception(f"Pipeline error: {exc}")
            return f"Error processing video: {str(exc)}"
    
    def process_video(self, video_input: VideoInput) -> str:
        """Alias for process()."""
        return self.process(video_input)
    
    def build_knowledge(self, job_id: str, title: str, items: list[str]) -> dict[str, Any]:
        """Build final knowledge from all processed videos."""
        try:
            logger.info(f"Building knowledge for job {job_id}")
            
            # Combine all items
            valid_items = [item for item in items if item and item.strip() and not item.startswith("Error")]
            
            if not valid_items:
                combined_doc = "No content could be extracted from the video(s)."
            else:
                combined_doc = "\n\n---\n\n".join(valid_items)
            
            return {
                "job_id": job_id,
                "title": title,
                "document": combined_doc,
                "status": "completed"
            }
        except Exception as exc:
            logger.exception(f"Knowledge building error: {exc}")
            return {
                "job_id": job_id,
                "title": title,
                "document": f"Error: {str(exc)}",
                "status": "failed"
            }