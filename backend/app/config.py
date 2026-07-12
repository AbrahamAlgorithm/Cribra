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


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )
