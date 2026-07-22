"""Ingestion pipeline types: DocumentSegment (2.1) and ExtractedDocument (2.2).

Implemented in Milestone 2, per SPEC.md Section 8.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel


class DocumentSegment(BaseModel):
    """One logically contiguous document isolated from a (possibly bundled) submission."""

    document_type: str
    page_start: int
    page_end: int
    text: str
    source_path: str
    # How each page's text within [page_start, page_end] was resolved
    # ("text" or "vision") — for audit, per SPEC.md Section 8's extraction-
    # method logging requirement. Populated by the pipeline after page
    # resolution; defaults to [] for callers that build a segment directly
    # (e.g. existing tests) without going through the full pipeline.
    page_methods: list[Literal["text", "vision"]] = []


class ExtractedDocument(BaseModel):
    """Output of field extraction (2.2) for one DocumentSegment.

    For certificate-type documents (CAC, Tax Clearance, PENCOM, ITF, NSITF):
    the generic schema fields are populated via GPT-4o, text or vision.
    For evidentiary documents (CVs, equipment schedules, etc.): only
    `normalized_text` is populated — these go through the RAG reasoning path
    (Milestone 4B), not the rule engine, so no structured fields are extracted.
    """

    document_type: str
    extraction_method: Literal["text", "vision"]
    holder_name: str | None = None
    identifier: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    normalized_text: str | None = None
    page_start: int
    page_end: int
    source_path: str
