"""Deterministic validation checks enforced in code (e.g. certificate expiry, SPEC.md 4.3).

Implemented in Milestone 4A. No LLM, no retrieval — plain code operating on
Milestone 2's structured `ExtractedDocument` output. Applies to the 5
certificate-type requirements (`segmentation.CERTIFICATE_DOCUMENT_TYPES`):
CAC, Tax Clearance, PENCOM, ITF, NSITF.
"""

from __future__ import annotations

from datetime import date

from app.ingestion.schema import ExtractedDocument


def validate_certificate(document: ExtractedDocument, evaluation_date: date) -> tuple[str, str]:
    """Deterministic per-document check per SPEC.md Section 4.3.

    Returns (status, justification) for a single ExtractedDocument. Two
    failure modes, both Non-Compliant, never a silent pass:
    - Expired: expiry_date is set and earlier than evaluation_date.
    - Missing evidence: extraction found neither a holder name nor an
      identifier — phases.md Phase 4A: "If a required field wasn't
      extracted at all (Phase 2 returned nulls), that's Non-Compliant."
      expiry_date alone isn't used for this check since some certificate
      types legitimately never have one (e.g. CAC/Certificate of
      Incorporation doesn't expire — confirmed on the real field-collected
      submission, which never had an expiry_date for its CAC segments).
    """
    if document.holder_name is None and document.identifier is None:
        return (
            "Non-Compliant",
            f"A {document.document_type} document was found in the submission "
            f"(pages {document.page_start}-{document.page_end}) but no holder name or "
            "identifier could be extracted from it — treated as missing evidence.",
        )

    if document.expiry_date is not None and document.expiry_date < evaluation_date:
        return (
            "Non-Compliant",
            f"{document.document_type} expired on {document.expiry_date}; "
            f"evaluated on {evaluation_date}.",
        )

    return (
        "Compliant",
        f"{document.document_type} is present and valid as of {evaluation_date}.",
    )
