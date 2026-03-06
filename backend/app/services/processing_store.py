from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class ProcessingRecord:
    status: str
    progress: float
    detail: str | None = None
    result: Any | None = None
    output_formats: list[str] = field(default_factory=list)


class ProcessingStore:
    def __init__(self) -> None:
        self._store: dict[str, ProcessingRecord] = {}
        self._lock = Lock()

    def create(self, job_id: str, status: str = "queued") -> None:
        with self._lock:
            self._store[job_id] = ProcessingRecord(status=status, progress=0.0)

    def update(self, job_id: str, *, status: str | None = None, progress: float | None = None, detail: str | None = None) -> None:
        with self._lock:
            record = self._store[job_id]
            if status is not None:
                record.status = status
            if progress is not None:
                record.progress = progress
            if detail is not None:
                record.detail = detail

    def set_result(self, job_id: str, result: Any, output_formats: list[str]) -> None:
        with self._lock:
            record = self._store[job_id]
            record.result = result
            record.output_formats = output_formats

    def get(self, job_id: str) -> ProcessingRecord | None:
        with self._lock:
            return self._store.get(job_id)
