"""Bundle segmentation (Phase 2.1): classify pages by document type, group
contiguous pages of the same type into logical documents.

Implemented in Milestone 2, per SPEC.md Section 8. Confirmed with the
procurement officer: contractor submissions arrive as a single bundled PDF,
often 100+ pages, containing every requirement's evidence together. This
module locates document boundaries inside that bundle so each requirement's
evidence can be extracted individually — it is cheap keyword/header pattern
matching, not a vector-search/RAG problem (that's Phase 3, and it indexes
the requirement corpus, not the submission).

Operates on already-resolved page text (see `page_resolver.py`, which runs
first and upgrades any page with insufficient extracted text via GPT-4o
vision) — this module itself never calls an LLM and doesn't care whether a
given page's text came from PyMuPDF/python-docx or vision transcription.
"""

from __future__ import annotations

from app.ingestion.schema import DocumentSegment

UNCLASSIFIED = "Unclassified"

# The five certificate-type requirements resolved by the deterministic rule
# engine (Milestone 4A) rather than RAG reasoning (Milestone 4B) — SPEC.md
# Section 4.1/4.3. field_extractor.py uses this to decide whether a segment
# gets structured-field extraction or just clean normalized text.
CERTIFICATE_DOCUMENT_TYPES = {
    "CAC Certificate",
    "Tax Clearance Certificate",
    "PENCOM Compliance Certificate",
    "ITF Compliance Certificate",
    "NSITF Compliance Certificate",
}

# Ordered so more specific patterns are checked before more generic ones
# (e.g. a PENCOM certificate's boilerplate could otherwise trip a looser
# "compliance certificate" match for the wrong type). First match wins.
_DOCUMENT_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "CAC Certificate",
        [
            "certificate of incorporation",
            "corporate affairs commission",
            "rc number",
        ],
    ),
    (
        "Tax Clearance Certificate",
        [
            "tax clearance certificate",
            "federal inland revenue service",
            "tcc number",
        ],
    ),
    (
        "PENCOM Compliance Certificate",
        [
            "national pension commission",
            "pencom",
            "pension commission",
        ],
    ),
    (
        "ITF Compliance Certificate",
        [
            "industrial training fund",
            "itf compliance",
        ],
    ),
    (
        "NSITF Compliance Certificate",
        [
            "nigeria social insurance trust fund",
            "nsitf",
        ],
    ),
    (
        "Audited Accounts",
        [
            "audited financial statement",
            "auditor's report",
            "auditors report",
            "statement of financial position",
            "independent auditor",
        ],
    ),
    (
        "Professional Registration",
        [
            "council for the regulation of engineering",
            "coren",
            "corbon",
            "professional registration",
        ],
    ),
    (
        "Key Personnel CVs",
        [
            "curriculum vitae",
            "cv of ",
        ],
    ),
    (
        "Similar Project Experience",
        [
            # "letter of award" confirmed against a real field-collected bundle
            # (phases.md, Phase 2.1) — the actual document uses this phrasing,
            # not the assumed "award letter". Kept both: real bundles vary.
            "letter of award",
            "award letter",
            "certificate of completion",
            "completion certificate",
            "similar project",
        ],
    ),
    (
        "Equipment Schedule",
        [
            "equipment schedule",
            "schedule of equipment",
            "list of equipment",
            "plant and equipment",
        ],
    ),
]


def classify_page(text: str) -> str | None:
    """Return the matched document type label, or None if no header matched."""
    lowered = text.lower()
    for label, patterns in _DOCUMENT_TYPE_PATTERNS:
        if any(pattern in lowered for pattern in patterns):
            return label
    return None


def segment_document(pages: list[str], source_path: str) -> list[DocumentSegment]:
    """Group contiguous pages into logical documents.

    A page with no recognized header inherits the current label forward
    (a CV or audited-accounts section often spans several pages without
    repeating its header). Pages before any label has been established, or
    any other run of unrecognized pages, are grouped under "Unclassified"
    and surfaced rather than dropped.
    """
    if not pages:
        return []

    segments: list[DocumentSegment] = []
    current_label: str | None = None
    current_start = 0
    current_pages: list[str] = []

    for index, page_text in enumerate(pages):
        detected = classify_page(page_text)
        effective_label = detected if detected is not None else (current_label or UNCLASSIFIED)

        if current_label is None:
            current_label = effective_label
            current_start = index
            current_pages = [page_text]
        elif effective_label != current_label:
            segments.append(
                DocumentSegment(
                    document_type=current_label,
                    page_start=current_start,
                    page_end=index - 1,
                    text="\n".join(current_pages),
                    source_path=source_path,
                )
            )
            current_label = effective_label
            current_start = index
            current_pages = [page_text]
        else:
            current_pages.append(page_text)

    if current_label is not None:
        segments.append(
            DocumentSegment(
                document_type=current_label,
                page_start=current_start,
                page_end=len(pages) - 1,
                text="\n".join(current_pages),
                source_path=source_path,
            )
        )

    return segments
