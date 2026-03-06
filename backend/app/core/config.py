from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Video2Knowledge AI"
    environment: str = "development"
    base_url: str = "http://localhost:8000"
    allow_network: bool = False
    storage_dir: Path = Path(__file__).resolve().parents[2] / "storage"
    uploads_dir: Path = storage_dir / "uploads"
    documents_dir: Path = storage_dir / "documents"
    frames_dir: Path = storage_dir / "frames"
    audio_dir: Path = storage_dir / "audio"
    max_upload_mb: int = 1024
    model_config = SettingsConfigDict(env_file=".env", env_prefix="V2K_", extra="ignore")


settings = Settings()
