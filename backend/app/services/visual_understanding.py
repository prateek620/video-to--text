from __future__ import annotations

from pathlib import Path

from app.services.models import FrameDescription


def describe_frames(frames: list[str]) -> list[FrameDescription]:
    """
    Lightweight production-safe placeholder:
    Uses filename/timestamp based descriptions instead of fake static samples.
    Replace with BLIP/LLaVA in next phase.
    """
    descriptions: list[FrameDescription] = []
    for frame in frames[:50]:
        p = Path(frame)
        if not p.exists():
            continue
        try:
            idx = int(p.stem.split("_")[-1])
            ts = max(0.0, (idx - 1) * 5.0)  # assuming fps=0.2
        except Exception:
            ts = 0.0
        descriptions.append(
            FrameDescription(
                timestamp=ts,
                description=f"Frame captured around {int(ts)}s from video segment.",
            )
        )
    return descriptions