from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse

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
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    if hostname in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
        return VideoSource.YOUTUBE
    if hostname in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        return VideoSource.VIMEO
    if hostname in {"dailymotion.com", "www.dailymotion.com"}:
        return VideoSource.DAILYMOTION
    if hostname == "drive.google.com":
        return VideoSource.GOOGLE_DRIVE
    if hostname in {"dropbox.com", "www.dropbox.com"}:
        return VideoSource.DROPBOX
    if parsed.scheme in {"http", "https"}:
        return VideoSource.DIRECT
    return VideoSource.UNKNOWN


def is_playlist(url: str) -> bool:
    lowered = url.lower()
    return "list=" in lowered or "playlist" in lowered


def download_from_url(
    url: str,
    output_dir: Path,
    *,
    allow_video_downloads: bool,
    cookies_from_browser: str = "",
) -> DownloadResult:
    if not allow_video_downloads:
        raise RuntimeError(
            "Video downloads are disabled. Set V2K_ALLOW_VIDEO_DOWNLOADS to a truthy value to enable downloads."
        )

    source = detect_source(url)
    playlist = is_playlist(url)
    output_template = str(output_dir / "%(title).200s-%(id)s.%(ext)s")
    ydl_opts: dict = {
        "outtmpl": output_template,
        "noplaylist": not playlist,
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

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
            path = Path(filename).with_suffix(".mp4")
            paths.append(path)
            metadata.append(
                VideoMetadata(
                    title=item.get("title"),
                    duration=item.get("duration"),
                    source_url=item.get("webpage_url"),
                )
            )

    return DownloadResult(paths=paths, metadata=metadata, source=source, is_playlist=playlist)