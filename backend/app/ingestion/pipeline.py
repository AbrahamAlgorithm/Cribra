"""Ingestion pipeline: orchestrates extraction, page resolution, preprocessing,
segmentation, and field extraction end to end.

Implemented in Milestone 2 (finalized architecture — SPEC.md Section 8).
"Done when: the full pipeline — bundle in, segmented and extracted documents
out — runs end to end" on the real 100+ page field-collected submission.

Confirmed against a real 158-page field-collected submission: it is a fully
scanned bundle with zero extractable text on any page. `page_resolver`
therefore runs before segmentation on every file, resolving each page's best
available text (PyMuPDF/python-docx first, GPT-4o vision fallback, cached
and concurrent) — segmentation only ever sees real text, never a raw
extraction that might be empty.

Known gap: Milestone 1's `routes_submissions.py` accepts standalone image
uploads (.jpg/.jpeg/.png) alongside PDF/DOCX, but the pipeline's segmentation
step is designed around *pages of a document* — it does not define how to
classify/segment a bare image upload with no page structure at all. Rather
than guess an unspecified behavior, this raises a clear error for image
files; flagged in the Milestone 2 update doc for a scoping decision.
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion import docx_extractor, page_resolver, pdf_extractor, preprocess
from app.ingestion.field_extractor import process_segment
from app.ingestion.schema import ExtractedDocument
from app.ingestion.segmentation import segment_document

_PAGE_EXTRACTORS = {
    ".pdf": pdf_extractor.extract_pages,
    ".docx": docx_extractor.extract_pages,
}


def process_document(path: str | Path) -> list[ExtractedDocument]:
    """Run the full Phase 2 pipeline: extract -> resolve -> preprocess -> segment -> extract fields."""
    path_str = str(path)
    suffix = Path(path_str).suffix.lower()

    extractor = _PAGE_EXTRACTORS.get(suffix)
    if extractor is None:
        raise ValueError(
            f"Unsupported file type for ingestion: '{suffix}'. Supported: "
            f"{sorted(_PAGE_EXTRACTORS)}. Standalone image uploads are not yet "
            "supported by the ingestion pipeline — see module docstring."
        )

    raw_pages = extractor(path_str)
    resolved_pages, page_methods = page_resolver.resolve_pages_sync(path_str, raw_pages)
    cleaned_pages = preprocess.clean_pages(resolved_pages)

    segments = segment_document(cleaned_pages, source_path=path_str)
    segments_with_methods = [
        segment.model_copy(update={"page_methods": page_methods[segment.page_start : segment.page_end + 1]})
        for segment in segments
    ]

    return [process_segment(segment) for segment in segments_with_methods]
