from __future__ import annotations

import os
from pathlib import Path

from app.services.models import Transcript, TranscriptSegment

_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL

    from faster_whisper import WhisperModel

    model_name = os.getenv("WHISPER_MODEL", "large-v3").strip() or "large-v3"
    device = os.getenv("WHISPER_DEVICE", "cuda").strip() or "cuda"
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16").strip() or "float16"

    _MODEL = WhisperModel(model_name, device=device, compute_type=compute_type)
    return _MODEL


def transcribe_audio(audio_path: str) -> Transcript:
    p = Path(audio_path)
    if not p.exists():
        raise RuntimeError(f"Audio not found: {audio_path}")

    model = _load_model()

    # TASK=translate forces English output even if source audio is Hindi/Spanish/etc.
    segments_iter, info = model.transcribe(
        str(p),
        task="translate",
        beam_size=3,
        best_of=3,
        temperature=0.0,
        vad_filter=True,
        word_timestamps=False,
        condition_on_previous_text=False,
    )

    segments: list[TranscriptSegment] = []
    for s in segments_iter:
        t = (s.text or "").strip()
        if t:
            segments.append(TranscriptSegment(start=float(s.start), end=float(s.end), text=t))

    if not segments:
        segments = [TranscriptSegment(start=0.0, end=0.0, text="No speech detected.")]

    # output language is English after task=translate
    return Transcript(segments=segments, language="en")