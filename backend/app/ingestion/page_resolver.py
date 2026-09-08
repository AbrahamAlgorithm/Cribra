"""Per-page text resolution: text-first, GPT-4o vision fallback, cached and concurrent.

Implemented in Milestone 2 (finalized architecture, SPEC.md Section 8 /
Ground Rules). Runs before segmentation so segmentation always has real text
(extracted or vision-transcribed) to keyword-match against — a real
158-page field-collected submission was found to have zero extractable text
on every page (a phone-scanned bundle), which segmentation cannot handle on
its own. No OCR library is used; the only fallback is GPT-4o vision, per the
real Tesseract-vs-vision comparison documented in SPEC.md Section 8.

Vision calls are batched concurrently (not sequential — 158 pages at
~5-20s each would make one evaluation impractically slow) and cached to
disk per rendered-page-image hash (see `vision_cache.py`) so repeated
development runs don't re-pay cost/time for unchanged pages.

Prompt text is authored in PROMPTS.md, Section 8, and mirrored here — keep
the two in sync.
"""

from __future__ import annotations

import asyncio
import base64
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

import openai
from openai import AsyncOpenAI

from app.config import get_settings
from app.ingestion import vision_cache
from app.ingestion.field_extractor import is_text_sufficient
from app.ingestion.pdf_extractor import render_page_image

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"

# Mirrors PROMPTS.md Section 8 — keep in sync.
_TRANSCRIBE_PROMPT = """\
You are transcribing a scanned page from a Nigerian government procurement \
document (a certificate, CV, equipment schedule, audited accounts, or \
similar contractor submission document).

Transcribe all visible text on this page image, as plainly and completely \
as possible. Preserve line breaks where they help readability. Do not \
summarize, interpret, or omit any text you can read, including headers, \
stamps, and watermarks. If part of the page is illegible, write [illegible] \
in that spot rather than guessing.

Return ONLY the transcribed text — no commentary, no JSON, no markdown \
formatting.\
"""

# A real, deterministic finding on the field-collected bundle: a genuinely
# upside-down scan of an official certificate (with a QR code) got a flat
# refusal from GPT-4o at 0deg — "I'm sorry, I can't assist with that" — on
# 3/3 attempts, not a transient fluke. Rotating the same image 180deg
# (correcting the orientation) transcribed it correctly on the first try.
# Presumed cause: the model's caution around unusual/inverted document
# images with a QR code, not any actual sensitive content — the certificate
# itself is an ordinary business compliance document. Retrying across
# rotations is cheap and fixes the real case found; a refusal must never be
# cached or treated as real page content, since that silently poisons
# classification for that page on every future run.
_ROTATIONS_TO_TRY = (0, 180, 90, 270)
_REFUSAL_MARKERS = (
    "i'm sorry",
    "i am sorry",
    "cannot assist",
    "can't assist",
    "cannot help with that",
    "can't help with that",
    "i cannot provide",
    "i can't provide",
    "unable to transcribe",
    "unable to read",
    "i'm unable to",
    "i am unable to",
)


def _looks_like_refusal(text: str) -> bool:
    stripped = text.strip().lower()
    return len(stripped) < 200 and any(marker in stripped for marker in _REFUSAL_MARKERS)


_render_pool: ThreadPoolExecutor | None = None
_render_pool_lock = threading.Lock()


def _get_render_pool() -> ThreadPoolExecutor:
    """Bounded pool for page rasterization.

    Deliberately bounded rather than using asyncio's default executor: every
    page of a bundle is rendered concurrently, and an unbounded fan-out holds
    that many full-page pixmaps in memory at once — enough to get a container
    OOM-killed on a 158-page bundle.
    """
    global _render_pool
    with _render_pool_lock:
        if _render_pool is None:
            _render_pool = ThreadPoolExecutor(
                max_workers=min(8, os.cpu_count() or 2),
                thread_name_prefix="page-render",
            )
        return _render_pool


async def _render(path: str, page_number: int, rotation: int) -> bytes:
    return await asyncio.get_running_loop().run_in_executor(
        _get_render_pool(), partial(render_page_image, path, page_number, rotation=rotation)
    )


_async_client: AsyncOpenAI | None = None


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(
            api_key=get_settings().openai_api_key,
            timeout=get_settings().openai_request_timeout_seconds,
        )
    return _async_client


async def _create_with_retry(**kwargs) -> object:
    """Retry on 429 rate-limit errors with exponential backoff.

    Live-tested against the real 158-page bundle: even at reduced
    concurrency, transient 429s are expected under a 30,000 TPM cap, and the
    first version of this pipeline had no retry at all — one rate-limited
    page crashed the entire 158-page run instead of just backing off.
    """
    settings = get_settings()
    for attempt in range(settings.openai_rate_limit_retries):
        try:
            return await _get_async_client().chat.completions.create(**kwargs)
        except openai.RateLimitError:
            if attempt == settings.openai_rate_limit_retries - 1:
                raise
            delay = settings.openai_retry_base_delay_seconds * (2**attempt)
            logger.warning(
                "Rate limited by OpenAI; retrying in %.1fs (attempt %d/%d).",
                delay,
                attempt + 1,
                settings.openai_rate_limit_retries,
            )
            await asyncio.sleep(delay)


async def _transcribe_image_bytes_raw(image_bytes: bytes) -> str:
    """One raw vision call — no caching, no refusal handling. Callers: below."""
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    response = await _create_with_retry(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": _TRANSCRIBE_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Transcribe this page."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


async def _transcribe_page(
    path: str, page_number: int, semaphore: asyncio.Semaphore, document_hash: str
) -> tuple[str, bool]:
    """Transcribe a page via vision, retrying with rotation if the model refuses.

    Returns (text, avoided_openai) — the flag feeds the cache hit-rate summary
    logged by `resolve_pages`. It is true when no OpenAI call was made at all,
    which covers both a cache hit and a page whose every rotation is a known
    refusal; the latter costs nothing on a repeat run but is not a hit.

    `semaphore` bounds concurrent OpenAI calls only. Rasterizing is CPU-bound
    and has no rate limit, so it is deliberately outside the semaphore and off
    the event loop: every page must be rendered just to compute its cache key,
    and doing that inline made a fully-cached 158-page run take ~50s of pure
    serialized CPU with no API calls at all.

    See the module-level comment above `_ROTATIONS_TO_TRY` for why rotation
    is the retry strategy. A refusal is never returned as real page text — if
    every rotation refuses, the page is left as empty text (so it stays
    "Unclassified" downstream rather than silently carrying a refusal
    message) and logged loudly for manual review.
    """
    # Keyed by document + page, so a page already resolved costs one small
    # file read and no rasterization at all.
    resolved_key = vision_cache.page_key(document_hash, page_number)
    already_resolved = vision_cache.get_cached(resolved_key)
    if already_resolved is not None:
        return already_resolved, True

    called_openai = False
    for rotation in _ROTATIONS_TO_TRY:
        image_bytes = await _render(path, page_number, rotation)
        image_hash = vision_cache.hash_image(image_bytes)

        if vision_cache.is_refusal_cached(image_hash):
            continue

        cached = vision_cache.get_cached(image_hash)
        if cached is not None and not _looks_like_refusal(cached):
            vision_cache.set_cached(resolved_key, cached)
            return cached, True

        called_openai = True
        async with semaphore:
            text = await _transcribe_image_bytes_raw(image_bytes)
        if not _looks_like_refusal(text):
            vision_cache.set_cached(image_hash, text)
            vision_cache.set_cached(resolved_key, text)
            return text, False

        vision_cache.set_refusal(image_hash)
        logger.warning(
            "GPT-4o vision refused page %d of %s at %d° rotation; trying next rotation.",
            page_number,
            path,
            rotation,
        )

    logger.error(
        "GPT-4o vision refused page %d of %s at every rotation tried %s. "
        "Leaving page text empty for manual review — it will not be classified.",
        page_number,
        path,
        _ROTATIONS_TO_TRY,
    )
    return "", not called_openai


async def resolve_pages(path: str, page_texts: list[str]) -> tuple[list[str], list[str]]:
    """Resolve the best available text for each page.

    Returns (texts, methods) — one entry per page, same order as input.
    methods[i] is "text" or "vision", for audit (same contract as
    ExtractedDocument.extraction_method in field_extractor.py).
    """
    is_pdf = Path(path).suffix.lower() == ".pdf"
    semaphore = asyncio.Semaphore(get_settings().openai_vision_concurrency)
    needs_vision = is_pdf and any(not is_text_sufficient(text) for text in page_texts)
    document_hash = await asyncio.to_thread(vision_cache.hash_file, path) if needs_vision else ""
    cache_hits = 0

    async def resolve_one(index: int, text: str) -> tuple[str, str]:
        nonlocal cache_hits
        if is_text_sufficient(text):
            return text, "text"
        if not is_pdf:
            # DOCX has no page-image concept to rasterize — same documented
            # tradeoff as field_extractor.py's certificate extraction fallback.
            logger.warning(
                "Insufficient text on non-PDF page %d of %s; no vision fallback available.",
                index,
                path,
            )
            return text, "text"
        transcribed, avoided_openai = await _transcribe_page(path, index, semaphore, document_hash)
        cache_hits += avoided_openai
        return transcribed, "vision"

    results = await asyncio.gather(*(resolve_one(i, t) for i, t in enumerate(page_texts)))
    if not results:
        return [], []
    texts, methods = (list(item) for item in zip(*results))

    # A silently-cold cache is the difference between a ~1 minute run and a
    # rate-limit-bound ~10 minute one, and it has a non-obvious trigger: the
    # cache is keyed by rendered image, so changing PDF_RENDER_ZOOM discards
    # every entry at once. Report the hit rate so that stays visible.
    vision_pages = sum(1 for method in methods if method == "vision")
    if vision_pages:
        logger.info(
            "Page resolution: %d/%d pages needed vision — %d needed no OpenAI "
            "call (cached), %d called OpenAI.",
            vision_pages,
            len(methods),
            cache_hits,
            vision_pages - cache_hits,
        )
    return texts, methods


def resolve_pages_sync(path: str, page_texts: list[str]) -> tuple[list[str], list[str]]:
    return asyncio.run(resolve_pages(path, page_texts))
