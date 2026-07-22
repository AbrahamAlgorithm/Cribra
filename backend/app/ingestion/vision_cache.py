"""Disk-backed cache for GPT-4o vision page-transcription results, keyed by a
hash of the rendered page image.

Implemented in Milestone 2 (finalized architecture) per SPEC.md Section 8,
Milestone 2 / Ground Rules: "cache vision results per page ... so repeated
development runs don't re-pay cost/time for unchanged pages." Disk-backed
(not just an in-process dict) so the cache survives process restarts during
development/tuning, which is the actual scenario this is meant to help with.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.config import get_settings


def hash_image(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _cache_dir() -> Path:
    path = Path(get_settings().vision_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_cached(image_hash: str) -> str | None:
    cache_file = _cache_dir() / f"{image_hash}.json"
    if not cache_file.exists():
        return None
    return json.loads(cache_file.read_text())["text"]


def set_cached(image_hash: str, text: str) -> None:
    cache_file = _cache_dir() / f"{image_hash}.json"
    cache_file.write_text(json.dumps({"text": text}))
