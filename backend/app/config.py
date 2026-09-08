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
    # Conservative defaults for accounts with modest TPM ceilings; configurable
    # per deployment without code changes.
    openai_vision_concurrency: int = 2
    openai_field_extraction_concurrency: int = 2
    openai_evaluation_concurrency: int = 2
    openai_rate_limit_retries: int = 3
    openai_retry_base_delay_seconds: float = 1.0
    openai_request_timeout_seconds: float = 60.0
    # Keep at 2.0. The vision cache is keyed by a hash of the rendered page
    # image, so changing this silently invalidates every cached page and
    # forces a full re-transcription of every document. It is also not a cost
    # lever: 1.5 and 2.0 both resize to the same 6 tiles (1105 tokens) on
    # GPT-4o's side, so lowering it saves no tokens and only loses fidelity.
    pdf_render_zoom: float = 2.0


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", str(BASE_DIR / "data" / "chroma")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        upload_dir=os.getenv("UPLOAD_DIR", str(BASE_DIR / "data" / "uploads")),
        vision_cache_dir=os.getenv("VISION_CACHE_DIR", str(BASE_DIR / "data" / "vision_cache")),
        openai_vision_concurrency=max(1, int(os.getenv("OPENAI_VISION_CONCURRENCY", "2"))),
        openai_field_extraction_concurrency=max(
            1, int(os.getenv("OPENAI_FIELD_EXTRACTION_CONCURRENCY", "2"))
        ),
        openai_evaluation_concurrency=max(1, int(os.getenv("OPENAI_EVALUATION_CONCURRENCY", "2"))),
        openai_rate_limit_retries=max(1, int(os.getenv("OPENAI_RATE_LIMIT_RETRIES", "6"))),
        openai_retry_base_delay_seconds=max(
            0.5, float(os.getenv("OPENAI_RETRY_BASE_DELAY_SECONDS", "1.0"))
        ),
        openai_request_timeout_seconds=max(
            5.0, float(os.getenv("OPENAI_REQUEST_TIMEOUT_SECONDS", "60.0"))
        ),
        pdf_render_zoom=max(1.0, float(os.getenv("PDF_RENDER_ZOOM", "2.0"))),
    )
