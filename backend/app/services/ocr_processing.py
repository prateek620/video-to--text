from __future__ import annotations

from pathlib import Path

import pytesseract
from PIL import Image, ImageOps

from app.services.models import FrameText

# If PATH fails, uncomment:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def _timestamp_from_frame_name(frame_path: Path, fps: float = 0.2) -> float:
    try:
        idx = int(frame_path.stem.split("_")[-1])  # frame_000123
    except Exception:
        return 0.0
    return max(0.0, (idx - 1) / fps)


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def extract_text_from_frames(frames: list[str]) -> list[FrameText]:
    out: list[FrameText] = []
    for f in frames:
        p = Path(f)
        if not p.exists():
            continue
        try:
            img = Image.open(p).convert("L")
            img = ImageOps.autocontrast(img)
            text = _clean(pytesseract.image_to_string(img, lang="eng"))
            if not text:
                continue
            out.append(FrameText(timestamp=_timestamp_from_frame_name(p), text=text))
        except Exception:
            continue
    return out