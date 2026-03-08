from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


class VideoSource(str, Enum):
    YOUTUBE = "youtube"
    VIMEO = "vimeo"
    DAILYMOTION = "dailymotion"
    GOOGLE_DRIVE = "google_drive"
    DROPBOX = "dropbox"
    DIRECT = "direct"
    UNKNOWN = "unknown"


@dataclass
class VideoMetadata:
    title: str | None
    duration: float | None
    source_url: str | None


@dataclass
class DownloadResult:
    paths: list[Path]
    metadata: list[VideoMetadata]
    source: VideoSource
    is_playlist: bool


class VideoDownloadDisabledError(RuntimeError):
    pass


class VideoDownloadError(RuntimeError):
    pass


def detect_source(url: str) -> VideoSource:
    host = (urlparse(url).hostname or "").lower()
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        return VideoSource.YOUTUBE
    if host in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        return VideoSource.VIMEO
    if host in {"dailymotion.com", "www.dailymotion.com"}:
        return VideoSource.DAILYMOTION
    if host == "drive.google.com":
        return VideoSource.GOOGLE_DRIVE
    if host in {"dropbox.com", "www.dropbox.com"}:
        return VideoSource.DROPBOX
    if urlparse(url).scheme in {"http", "https"}:
        return VideoSource.DIRECT
    return VideoSource.UNKNOWN


def is_playlist(url: str) -> bool:
    low = url.lower()
    return "list=" in low or "playlist" in low


def _download_items(url: str, ydl_opts: dict[str, Any]) -> tuple[list[Path], list[VideoMetadata]]:
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        entries = info.get("entries") if isinstance(info, dict) else None
        items = [e for e in entries if e] if entries else [info]

        paths: list[Path] = []
        metadata: list[VideoMetadata] = []
        for item in items:
            if not item:
                continue
            base = Path(ydl.prepare_filename(item))
            merge_ext = ydl_opts.get("merge_output_format")
            final_path = base.with_suffix(f".{merge_ext}") if isinstance(merge_ext, str) and merge_ext else base
            paths.append(final_path)
            metadata.append(
                VideoMetadata(
                    title=item.get("title"),
                    duration=item.get("duration"),
                    source_url=item.get("webpage_url") or item.get("original_url"),
                )
            )
    return paths, metadata


def download_from_url(
    url: str,
    output_dir: Path,
    *,
    allow_video_downloads: bool,
    cookies_from_browser: str = "",
) -> DownloadResult:
    if not allow_video_downloads:
        raise VideoDownloadDisabledError("Enable V2K_ALLOW_VIDEO_DOWNLOADS=true in backend .env")

    output_dir.mkdir(parents=True, exist_ok=True)
    source = detect_source(url)
    playlist = is_playlist(url)

    ydl_opts: dict[str, Any] = {
        "outtmpl": str(output_dir / "%(title).160s-%(id)s.%(ext)s"),
        "noplaylist": not playlist,
        "quiet": False,
        "no_warnings": False,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",
        "merge_output_format": "mp4",
    }

    # Windows-safe: do not use browser cookies unless explicitly needed and non-Windows
    if cookies_from_browser:
        import platform

        if platform.system().lower() != "windows":
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    try:
        paths, metadata = _download_items(url, ydl_opts)
    except DownloadError as exc:
        raise VideoDownloadError(f"Failed to download URL: {exc}") from exc

    return DownloadResult(paths=paths, metadata=metadata, source=source, is_playlist=playlist)