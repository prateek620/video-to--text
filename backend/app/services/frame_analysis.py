from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.config import settings
from app.services.file_utils import ensure_dir
from app.services.models import SceneChange


def extract_frames(video_path: str, fps: float = 0.2) -> list[str]:
    video = Path(video_path)
    if not video.exists():
        raise RuntimeError(f"Video not found: {video_path}")

    ensure_dir(settings.frames_dir)
    clip_dir = settings.frames_dir / video.stem
    ensure_dir(clip_dir)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg is required for frame extraction.")

    output_pattern = str(clip_dir / "frame_%06d.jpg")
    cmd = [ffmpeg, "-y", "-i", str(video), "-vf", f"fps={fps}", "-q:v", "2", output_pattern]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or str(exc)).strip()
        raise RuntimeError(f"ffmpeg failed to extract frames from {video.name}: {err}") from exc

    frames = sorted(clip_dir.glob("frame_*.jpg"))
    return [str(p) for p in frames]


def detect_scenes(frames: list[str]) -> list[SceneChange]:
    if not frames:
        return []
    n = len(frames)
    ids = sorted(set([0, n // 2, n - 1]))
    labels = ["Opening", "Middle", "Summary"]
    return [SceneChange(timestamp=float(i * 5), label=labels[min(k, 2)]) for k, i in enumerate(ids)]