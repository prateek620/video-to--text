from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def transcribe(audio_path: str) -> str:
    """Convert audio file to text using Whisper (local, no internet required)."""
    try:
        import whisper
        
        logger.info(f"Loading Whisper model...")
        model = whisper.load_model("base")
        
        logger.info(f"Transcribing audio: {audio_path}")
        result = model.transcribe(audio_path, language="en")
        
        text = result.get("text", "").strip()
        logger.info(f"Successfully transcribed audio: {len(text)} characters")
        return text if text else "No speech detected in audio"
            
    except ImportError:
        logger.error("whisper library not installed. Install with: pip install openai-whisper")
        return "Whisper not available"
    except Exception as e:
        logger.exception(f"Transcription error: {e}")
        return f"Transcription failed: {str(e)}"