from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4


def safe_filename(filename: str | None, default_ext: str = ".bin") -> str:
    if not filename:
        return f"upload-{uuid4().hex}{default_ext}"
    name = Path(filename).name
    name = re.sub(r"[^A-Za-z0-9._-]+", "-", name)
    return f"{uuid4().hex}-{name}"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
