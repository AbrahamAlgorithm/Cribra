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
from pathlib import Path

import openai
from openai import AsyncOpenAI

from app.config import get_settings
from app.ingestion import vision_cache
from app.ingestion.field_extractor import is_text_sufficient
from app.ingestion.pdf_extractor import render_page_image

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"

# SPEC.md Section 8 specified "~15-20 in flight" assuming enough headroom on
# the account's rate limit. Live-tested against the real 158-page bundle and
# found this account is capped at 30,000 TPM for gpt-4o — 15 full-page
# vision requests fired at once exhausts that immediately (measured: 30000/30000
# used, a 923-token request rejected). Lowered to a concurrency this account
# can actually sustain, plus retry-with-backoff below for the residual risk
# of hitting the cap anyway.
MAX_CONCURRENT_VISION_CALLS = 5

_MAX_RATE_LIMIT_RETRIES = 6
_RETRY_BASE_DELAY_SECONDS = 3.0

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


_async_client: AsyncOpenAI | None = None


def _get_async_client() -> AsyncOpenAI:
    global _async_client
    if _async_client is None:
        _async_client = AsyncOpenAI(api_key=get_settings().openai_api_key)
    return _async_client


async def _create_with_retry(**kwargs) -> object:
    """Retry on 429 rate-limit errors with exponential backoff.

    Live-tested against the real 158-page bundle: even at reduced
    concurrency, transient 429s are expected under a 30,000 TPM cap, and the
    first version of this pipeline had no retry at all — one rate-limited
    page crashed the entire 158-page run instead of just backing off.
    """
    for attempt in range(_MAX_RATE_LIMIT_RETRIES):
        try:
            return await _get_async_client().chat.completions.create(**kwargs)
        except openai.RateLimitError:
            if attempt == _MAX_RATE_LIMIT_RETRIES - 1:
                raise
            delay = _RETRY_BASE_DELAY_SECONDS * (2**attempt)
            logger.warning(
                "Rate limited by OpenAI; retrying in %.1fs (attempt %d/%d).",
                delay,
                attempt + 1,
                _MAX_RATE_LIMIT_RETRIES,
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


async def _transcribe_page(path: str, page_number: int) -> str:
    """Transcribe a page via vision, retrying with rotation if the model refuses.

    See the module-level comment above `_ROTATIONS_TO_TRY` for why rotation
    is the retry strategy. A refusal is never cached and never returned as
    real page text — if every rotation refuses, the page is left as empty
    text (so it stays "Unclassified" downstream rather than silently
    carrying a refusal message) and logged loudly for manual review.
    """
    for rotation in _ROTATIONS_TO_TRY:
        image_bytes = render_page_image(path, page_number, rotation=rotation)
        image_hash = vision_cache.hash_image(image_bytes)

        cached = vision_cache.get_cached(image_hash)
        if cached is not None and not _looks_like_refusal(cached):
            return cached

        text = await _transcribe_image_bytes_raw(image_bytes)
        if not _looks_like_refusal(text):
            vision_cache.set_cached(image_hash, text)
            return text

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
    return ""


async def resolve_pages(path: str, page_texts: list[str]) -> tuple[list[str], list[str]]:
    """Resolve the best available text for each page.

    Returns (texts, methods) — one entry per page, same order as input.
    methods[i] is "text" or "vision", for audit (same contract as
    ExtractedDocument.extraction_method in field_extractor.py).
    """
    is_pdf = Path(path).suffix.lower() == ".pdf"
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_VISION_CALLS)

    async def resolve_one(index: int, text: str) -> tuple[str, str]:
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
        async with semaphore:
            transcribed = await _transcribe_page(path, index)
            return transcribed, "vision"

    results = await asyncio.gather(*(resolve_one(i, t) for i, t in enumerate(page_texts)))
    if not results:
        return [], []
    texts, methods = (list(item) for item in zip(*results))
    return texts, methods


def resolve_pages_sync(path: str, page_texts: list[str]) -> tuple[list[str], list[str]]:
    return asyncio.run(resolve_pages(path, page_texts))
