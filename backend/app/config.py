"""Application configuration, loaded once from environment variables (.env)."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    openai_api_key: str = ""
    chroma_persist_dir: str = str(BASE_DIR / "data" / "chroma")
    log_level: str = "INFO"
    # Not part of the frozen .env.example contract (SPEC.md Section 8, Milestone 0) —
    # optional override, defaults to a path under the repo so no .env change is required.
    upload_dir: str = str(BASE_DIR / "data" / "uploads")
    # Disk-backed cache for GPT-4o vision page-transcription results (SPEC.md
    # Section 8, Milestone 2: "cache vision results per page ... so repeated
    # development runs don't re-pay cost/time for unchanged pages").
    vision_cache_dir: str = str(BASE_DIR / "data" / "vision_cache")


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        upload_dir=os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")),
        vision_cache_dir=os.getenv("VISION_CACHE_DIR", str(BASE_DIR / "data" / "vision_cache")),
    )
