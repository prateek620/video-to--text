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


def _is_cookie_load_error(exc: DownloadError) -> bool:
    message = str(exc).lower()
    return "failed to load cookies" in message or "failed to decrypt with dpapi" in message


def _is_format_unavailable_error(exc: DownloadError) -> bool:
    return "requested format is not available" in str(exc).lower()


def _format_fallback_options(base_options: dict[str, Any]) -> list[dict[str, Any]]:
    retries: list[dict[str, Any]] = []

    broader_mp4_options = base_options.copy()
    broader_mp4_options["format"] = "bestvideo*+bestaudio/best"
    retries.append(broader_mp4_options)

    best_single_stream_options = base_options.copy()
    best_single_stream_options["format"] = "best"
    best_single_stream_options.pop("merge_output_format", None)
    retries.append(best_single_stream_options)

    default_selector_options = base_options.copy()
    default_selector_options.pop("format", None)
    default_selector_options.pop("merge_output_format", None)
    retries.append(default_selector_options)

    return retries


def _download_items(url: str, ydl_opts: dict[str, Any]) -> tuple[list[Path], list[VideoMetadata]]:
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
            path = Path(filename)
            merge_extension = ydl_opts.get("merge_output_format")
            if isinstance(merge_extension, str) and merge_extension:
                path = path.with_suffix(f".{merge_extension}")
            paths.append(path)
            metadata.append(
                VideoMetadata(
                    title=item.get("title"),
                    duration=item.get("duration"),
                    source_url=item.get("webpage_url"),
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
        raise VideoDownloadDisabledError(
            "Video downloads are disabled. Set V2K_ALLOW_VIDEO_DOWNLOADS to a truthy value to enable downloads."
        )

    source = detect_source(url)
    playlist = is_playlist(url)
    output_template = str(output_dir / "%(title).200s-%(id)s.%(ext)s")
    ydl_opts: dict[str, Any] = {
        "outtmpl": output_template,
        "noplaylist": not playlist,
        "quiet": True,
        "no_warnings": True,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
    }

    if cookies_from_browser:
        ydl_opts["cookiesfrombrowser"] = (cookies_from_browser,)

    try:
        paths, metadata = _download_items(url, ydl_opts)
    except DownloadError as exc:
        if _is_format_unavailable_error(exc):
            for fallback_opts in _format_fallback_options(ydl_opts):
                try:
                    paths, metadata = _download_items(url, fallback_opts)
                    return DownloadResult(paths=paths, metadata=metadata, source=source, is_playlist=playlist)
                except DownloadError as fallback_exc:
                    if not _is_format_unavailable_error(fallback_exc):
                        raise VideoDownloadError(
                            "Failed to download the provided URL. Check the link and try again."
                        ) from fallback_exc

            raise VideoDownloadError(
                "Failed to download the provided URL. No compatible video format was available."
            ) from exc

        if cookies_from_browser and _is_cookie_load_error(exc):
            fallback_opts = ydl_opts.copy()
            fallback_opts.pop("cookiesfrombrowser", None)
            try:
                paths, metadata = _download_items(url, fallback_opts)
            except DownloadError as fallback_exc:
                raise VideoDownloadError(
                    "Failed to download the provided URL after retrying without browser cookies. "
                    "Try another link or disable V2K_COOKIES_FROM_BROWSER in backend .env."
                ) from fallback_exc
        else:
            raise VideoDownloadError("Failed to download the provided URL. Check the link and try again.") from exc

    return DownloadResult(paths=paths, metadata=metadata, source=source, is_playlist=playlist)
