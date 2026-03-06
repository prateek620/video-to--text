from __future__ import annotations

from app.services.models import SceneChange


SAMPLE_SCENES = [
    SceneChange(timestamp=0.0, label="Opening"),
    SceneChange(timestamp=90.0, label="Core Explanation"),
    SceneChange(timestamp=210.0, label="Summary"),
]


def extract_frames(_: str) -> list[str]:
    return ["frame_0.png", "frame_90.png", "frame_210.png"]


def detect_scenes(_: list[str]) -> list[SceneChange]:
    return SAMPLE_SCENES
