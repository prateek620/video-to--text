from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, field_validator

class Settings(BaseSettings):
    # API Settings
    app_name: str = "Video2Knowledge AI"
    api_title: str = "Video2Knowledge AI"
    api_version: str = "1.0.0"
    
    # Directory Settings (as Path objects)
    storage_dir: Path = Path(__file__).parent.parent.parent / "storage"
    uploads_dir: Path = Path(__file__).parent.parent.parent / "storage" / "uploads"
    documents_dir: Path = Path(__file__).parent.parent.parent / "storage" / "documents"
    frames_dir: Path = Path(__file__).parent.parent.parent / "storage" / "frames"
    audio_dir: Path = Path(__file__).parent.parent.parent / "storage" / "audio"
    
    # Feature Flags
    allow_video_downloads: bool = True
    cookies_from_browser: str = ""
    
    # Pydantic v2 config
    model_config = ConfigDict(
        env_file=".env",
        extra="ignore",
        arbitrary_types_allowed=True
    )
    
    @field_validator("storage_dir", "uploads_dir", "documents_dir", "frames_dir", "audio_dir", mode="before")
    @classmethod
    def validate_paths(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

settings = Settings()