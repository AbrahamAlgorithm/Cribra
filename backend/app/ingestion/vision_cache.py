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


def hash_file(path: str | Path) -> str:
    """Fingerprint a source document, for keying resolved text per page.

    Rasterizing a page costs ~325ms and PyMuPDF holds the GIL throughout, so
    on a fully cached 158-page bundle the rendering done purely to compute
    image cache keys dominated the entire run. Fingerprinting the file once
    gives a key that needs no rendering at all.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def page_key(document_hash: str, page_number: int) -> str:
    return f"{document_hash}-p{page_number}"


def _cache_dir() -> Path:
    path = Path(get_settings().vision_cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read(image_hash: str) -> dict | None:
    cache_file = _cache_dir() / f"{image_hash}.json"
    if not cache_file.exists():
        return None
    return json.loads(cache_file.read_text())


def get_cached(image_hash: str) -> str | None:
    """Cached transcription text, or None if absent or a known refusal.

    A refusal never comes back as text — see `is_refusal_cached`.
    """
    entry = _read(image_hash)
    if entry is None or entry.get("refused"):
        return None
    return entry["text"]


def set_cached(image_hash: str, text: str) -> None:
    cache_file = _cache_dir() / f"{image_hash}.json"
    cache_file.write_text(json.dumps({"text": text}))


def is_refusal_cached(image_hash: str) -> bool:
    """Whether GPT-4o already refused this exact rendered image.

    Refusals were found to be deterministic per image, not transient (see
    page_resolver's `_ROTATIONS_TO_TRY` comment: 3/3 refusals at 0deg on the
    same certificate). Recording them lets a repeat run skip straight to the
    rotation that works instead of re-paying every refused rotation's API
    call on every single run. Stored under a `refused` flag rather than as
    page text, so a refusal can never leak into a document's content;
    entries written before this flag existed simply read as non-refusals.
    """
    entry = _read(image_hash)
    return bool(entry is not None and entry.get("refused"))


def set_refusal(image_hash: str) -> None:
    cache_file = _cache_dir() / f"{image_hash}.json"
    cache_file.write_text(json.dumps({"text": "", "refused": True}))
