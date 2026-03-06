from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from yt_dlp import YoutubeDL


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


def detect_source(url: str) -> VideoSource:
    lowered = url.lower()
    if "youtube.com" in lowered or "youtu.be" in lowered:
        return VideoSource.YOUTUBE
    if "vimeo.com" in lowered:
        return VideoSource.VIMEO
    if "dailymotion.com" in lowered:
        return VideoSource.DAILYMOTION
    if "drive.google.com" in lowered:
        return VideoSource.GOOGLE_DRIVE
    if "dropbox.com" in lowered:
        return VideoSource.DROPBOX
    if lowered.startswith("http"):
        return VideoSource.DIRECT
    return VideoSource.UNKNOWN


def is_playlist(url: str) -> bool:
    lowered = url.lower()
    return "list=" in lowered or "playlist" in lowered


def download_from_url(url: str, output_dir: Path, *, allow_network: bool) -> DownloadResult:
    if not allow_network:
        raise RuntimeError("Network access disabled. Set V2K_ALLOW_NETWORK=true to enable downloads.")

    source = detect_source(url)
    playlist = is_playlist(url)
    output_template = str(output_dir / "%(title).200B-%(id)s.%(ext)s")
    ydl_opts = {
        "outtmpl": output_template,
        "noplaylist": not playlist,
        "quiet": True,
        "no_warnings": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        entries = info.get("entries") if isinstance(info, dict) else None
        if entries:
            items = [entry for entry in entries if entry]
        else:
            items = [info]

        paths: list[Path] = []
        metadata: list[VideoMetadata] = []
        for item in items:
            if not item:
                continue
            filename = ydl.prepare_filename(item)
            paths.append(Path(filename))
            metadata.append(
                VideoMetadata(
                    title=item.get("title"),
                    duration=item.get("duration"),
                    source_url=item.get("webpage_url"),
                )
            )

    return DownloadResult(paths=paths, metadata=metadata, source=source, is_playlist=playlist)
