from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

def fuse(transcript: str, frame_insights: list[dict], video_path: str) -> dict[str, Any]:
    """Intelligently combine audio transcript with visual scene descriptions."""
    try:
        logger.info("Fusing multimodal data...")
        
        if not transcript or not transcript.strip():
            logger.warning("Empty transcript")
            return {
                "transcript": "",
                "frame_insights": frame_insights,
                "combined_knowledge": "No audio content detected in video.",
                "video_path": video_path
            }
        
        # The transcript IS the main content for students
        # We just enhance it with any visual context
        combined = transcript
        
        # If we have meaningful scene descriptions, add them as context
        if frame_insights:
            real_scenes = [f for f in frame_insights 
                          if f.get("description", "").lower() not in ['opening', 'middle', 'summary', '']]
            
            if real_scenes:
                combined += "\n\nVisual Context from Video:\n"
                for scene in real_scenes:
                    desc = scene.get("description", "").strip()
                    if desc and desc.lower() not in ['opening', 'middle', 'summary']:
                        combined += f"- {desc}\n"
        
        return {
            "transcript": transcript,
            "frame_insights": frame_insights,
            "combined_knowledge": combined,
            "video_path": video_path
        }
        
    except Exception as e:
        logger.exception(f"Fusion error: {e}")
        return {
            "transcript": transcript,
            "frame_insights": frame_insights,
            "combined_knowledge": transcript,
            "video_path": video_path
        }
