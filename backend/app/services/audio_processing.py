from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.config import settings
from app.services.file_utils import ensure_dir


def extract_audio(video_path: Path) -> Path:
    ensure_dir(settings.audio_dir)
    output_path = settings.audio_dir / f"{video_path.stem}.wav"
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for audio extraction.")

    command = [
        ffmpeg,
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_path),
    ]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        error_output = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"ffmpeg failed to extract audio from {video_path.name}: {error_output}") from exc
    return output_path
