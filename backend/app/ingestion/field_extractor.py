"""Structured field extraction (Phase 2.2): text-first, vision-fallback.

Implemented in Milestone 2, per SPEC.md Section 8 / phases.md Phase 2.2.
Certificate-type segments (CAC, Tax Clearance, PENCOM, ITF, NSITF) get the
generic structured schema populated via GPT-4o (temperature 0). Evidentiary
segments (CVs, equipment schedules, etc.) just get clean normalized text —
they go through the RAG reasoning path (Milestone 4B), not the rule engine.

Prompt text is authored in PROMPTS.md, Sections 6-7, and mirrored here —
keep the two in sync.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from pathlib import Path

import openai
from openai import OpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.ingestion.pdf_extractor import render_page_image
from app.ingestion.schema import DocumentSegment, ExtractedDocument
from app.ingestion.segmentation import CERTIFICATE_DOCUMENT_TYPES

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"

# "Defined threshold — not hand-waved" per SPEC.md Section 8: a minimum
# character count plus a basic garbage-text check. Initial values; tune
# empirically once real field-collected documents are available, same as
# the chunk size/overlap defaults in chunker.py.
_MIN_SUFFICIENT_CHARS = 200
_MIN_ALPHANUMERIC_RATIO = 0.5

# Live-tested against the real 158-page bundle (see page_resolver.py): this
# account is capped at 30,000 TPM for gpt-4o, and a burst of vision calls
# during segmentation can leave no headroom for the extraction calls that
# follow immediately after. Same retry treatment as page_resolver.py.
_MAX_RATE_LIMIT_RETRIES = 6
_RETRY_BASE_DELAY_SECONDS = 3.0

# Mirrors PROMPTS.md Section 6 — keep in sync.
_TEXT_SYSTEM_PROMPT = """\
You are extracting structured fields from a Nigerian government-issued \
compliance certificate (CAC, Tax Clearance, PENCOM, ITF, or NSITF).

Given the certificate text below, extract exactly these fields as a JSON object:
- document_type: the specific certificate type (e.g. "CAC Certificate", "Tax \
Clearance Certificate", "PENCOM Compliance Certificate", "ITF Compliance \
Certificate", "NSITF Compliance Certificate")
- holder_name: the name of the company/contractor the certificate was issued to
- identifier: the certificate's unique identifier (RC number, TCC number, \
certificate number — whichever applies to this document type)
- issue_date: the date the certificate was issued, as YYYY-MM-DD, or null if \
not stated
- expiry_date: the date the certificate expires, as YYYY-MM-DD, or null if \
not stated or if the certificate does not expire

Return ONLY a JSON object with exactly these five keys. If a field cannot be \
determined from the text, use null for that field — never guess or fabricate \
a value.\
"""

# Mirrors PROMPTS.md Section 7 — keep in sync.
_VISION_SYSTEM_PROMPT = """\
You are extracting structured fields from an image of a Nigerian \
government-issued compliance certificate (CAC, Tax Clearance, PENCOM, ITF, \
or NSITF).

Look at the attached certificate image and extract exactly these fields as a \
JSON object:
- document_type: the specific certificate type (e.g. "CAC Certificate", "Tax \
Clearance Certificate", "PENCOM Compliance Certificate", "ITF Compliance \
Certificate", "NSITF Compliance Certificate")
- holder_name: the name of the company/contractor the certificate was issued to
- identifier: the certificate's unique identifier (RC number, TCC number, \
certificate number — whichever applies to this document type)
- issue_date: the date the certificate was issued, as YYYY-MM-DD, or null if \
not stated
- expiry_date: the date the certificate expires, as YYYY-MM-DD, or null if \
not stated or if the certificate does not expire

Return ONLY a JSON object with exactly these five keys. If a field cannot be \
read from the image, use null for that field — never guess or fabricate a \
value.\
"""

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=get_settings().openai_api_key)
    return _client


class _LLMFields(BaseModel):
    document_type: str | None = None
    holder_name: str | None = None
    identifier: str | None = None
    issue_date: str | None = None
    expiry_date: str | None = None


def is_text_sufficient(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < _MIN_SUFFICIENT_CHARS:
        return False
    alnum_count = sum(1 for ch in stripped if ch.isalnum())
    return (alnum_count / len(stripped)) >= _MIN_ALPHANUMERIC_RATIO


def _parse_llm_fields(raw_json: str) -> _LLMFields:
    return _LLMFields.model_validate(json.loads(raw_json))


def _create_with_retry(**kwargs) -> object:
    """Retry on 429 rate-limit errors with exponential backoff (sync)."""
    for attempt in range(_MAX_RATE_LIMIT_RETRIES):
        try:
            return _get_client().chat.completions.create(**kwargs)
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
            time.sleep(delay)


def _extract_fields_from_text(text: str) -> _LLMFields:
    response = _create_with_retry(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _TEXT_SYSTEM_PROMPT},
            {"role": "user", "content": f"Certificate text:\n\n{text}"},
        ],
    )
    return _parse_llm_fields(response.choices[0].message.content)


def _extract_fields_from_image(image_bytes: bytes) -> _LLMFields:
    image_b64 = base64.b64encode(image_bytes).decode("ascii")
    response = _create_with_retry(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the fields from this certificate image."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                ],
            },
        ],
    )
    return _parse_llm_fields(response.choices[0].message.content)


def process_segment(segment: DocumentSegment) -> ExtractedDocument:
    if segment.document_type not in CERTIFICATE_DOCUMENT_TYPES:
        return ExtractedDocument(
            document_type=segment.document_type,
            extraction_method="text",
            normalized_text=segment.text,
            page_start=segment.page_start,
            page_end=segment.page_end,
            source_path=segment.source_path,
        )

    is_pdf = Path(segment.source_path).suffix.lower() == ".pdf"

    if is_text_sufficient(segment.text):
        fields = _extract_fields_from_text(segment.text)
        method = "text"
    elif is_pdf:
        # Certificates are single-page in practice; rasterize the segment's
        # first page. Multi-page vision fallback isn't built — it doesn't
        # arise for any of the five certificate types.
        image_bytes = render_page_image(segment.source_path, segment.page_start)
        fields = _extract_fields_from_image(image_bytes)
        method = "vision"
    else:
        # DOCX has no page-image concept to rasterize. DOCX is a text-native
        # format, so insufficient extracted text here means a near-empty
        # document, not a scan — best-effort text extraction, logged.
        logger.warning(
            "Insufficient text extracted from non-PDF source %s; no vision "
            "fallback available for this format, proceeding best-effort.",
            segment.source_path,
        )
        fields = _extract_fields_from_text(segment.text)
        method = "text"

    return ExtractedDocument(
        document_type=segment.document_type,
        extraction_method=method,
        holder_name=fields.holder_name,
        identifier=fields.identifier,
        issue_date=fields.issue_date,
        expiry_date=fields.expiry_date,
        normalized_text=segment.text,
        page_start=segment.page_start,
        page_end=segment.page_end,
        source_path=segment.source_path,
    )
