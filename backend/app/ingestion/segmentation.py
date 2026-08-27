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

# Recognized by segmentation but NOT part of the 10-item default checklist
# (SPEC.md Section 4.1). Found in the real field-collected bundle — SCUML
# (Special Control Unit Against Money Laundering) isn't mentioned anywhere in
# that bundle's own table of contents, so it's a genuine "extra" document, not
# an omission on the officer's part. Segmentation still gives it its own
# correct label — rather than letting it silently pollute whatever certificate
# segment precedes it — so a future compliance report (Milestone 4B) can
# surface it as an observation ("found, not evaluated") instead of it being
# invisible or, worse, corrupting an actual required certificate's extracted
# text.
#
# "Interim Registration Report (BPP)" is here too, but its status is
# different: it's the same "BPP" line item SPEC.md Section 4.1 flags as an
# open question ("clarify whether 'BPP' ... needs a dedicated line item").
# The real bundle's own table of contents lists it as item 6, which is
# real evidence it probably *should* become an official checklist item — but
# that's a decision for the spec owner, not something to silently assume
# here. Kept in this "recognized, not (yet) required" set until that's
# decided; move it to CERTIFICATE_DOCUMENT_TYPES or its own evidentiary
# category if/when it's added to the default checklist.
NON_CHECKLIST_DOCUMENT_TYPES = {
    "Special Control Unit Against Money Laundering (SCUML)",
    "Interim Registration Report (BPP)",
}

# Ordered so more specific patterns are checked before more generic ones
# (e.g. a PENCOM certificate's boilerplate could otherwise trip a looser
# "compliance certificate" match for the wrong type). First match wins.
_DOCUMENT_TYPE_PATTERNS: list[tuple[str, list[str]]] = [
    (
        "CAC Certificate",
        [
            "certificate of incorporation",
            "rc number",
            # Bare "corporate affairs commission" was dropped (Milestone 6
            # prep, real-data validation on two additional field-collected
            # bundles): it matched narrative mentions inside Audited Accounts
            # notes ("...was incorporated with the Corporate Affairs
            # Commission on...") and company-overview pages, mislabeling
            # unrelated content as a CAC Certificate — same incidental-
            # mention lesson as the "coren"/"pencom" fixes above/below.
            # "certificate of incorporation" alone still matches every real
            # certificate's opening page; the rest of each bundle (subscriber
            # lists, director particulars, etc., none of which repeat the
            # header) already inherits forward correctly.
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
        # Checked before PENCOM/ITF/NSITF, whose patterns include bare
        # acronyms ("nsitf") needed to match their own acronym-only section
        # dividers. The real BPP Interim Registration Report's own
        # compliance-summary table lists PENCOM/NSITF/ITF as column headers
        # ("Compliant with 3 personnel, as obtained from PENCOM") — without
        # this ordering, that table would false-positive-match whichever of
        # those three happens to be checked first, exactly as the bare
        # "pencom" acronym did before this reordering (see PENCOM's comment
        # below). "interim registration report" / "bureau of public
        # procurement" are specific enough to this one document that
        # checking them first is safe.
        #
        # Not part of the 10-item default checklist — see
        # NON_CHECKLIST_DOCUMENT_TYPES above. Confirmed real phrasing: the
        # section divider reads "EVIDENCE OF REGISTRATION WITH BPP"; the
        # actual certificate reads "Interim Registration Report (IRR)...
        # BUREAU OF PUBLIC PROCUREMENT... www.bpp.gov.ng".
        "Interim Registration Report (BPP)",
        [
            "interim registration report",
            "bureau of public procurement",
            "registration with bpp",
        ],
    ),
    (
        "PENCOM Compliance Certificate",
        [
            "national pension commission",
            "pension commission",
            # Confirmed against the real bundle: the section-divider page
            # reads "EVIDENCE OF PENSION COMPLIANCE CERTIFICATE" — note
            # "compliance", not "commission". Without this, the divider page
            # matched nothing and silently inherited whatever label preceded
            # PENCOM instead of joining the PENCOM segment.
            "pension compliance",
            # Bare "pencom" was dropped: the real BPP Interim Registration
            # Report's own compliance-summary table has "PENCOM" as a column
            # header, which misclassified that certificate's own page as
            # PENCOM instead of BPP — same incidental-acronym-mention lesson
            # as the "coren"/"corbon" fix. (NSITF below still needs its own
            # bare acronym for its acronym-only divider page — handled by
            # checking BPP first instead, see the comment above.)
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
        # Not part of the 10-item default checklist — see
        # NON_CHECKLIST_DOCUMENT_TYPES above. Confirmed real phrasing:
        # "SPECIAL CONTROL UNIT AGAINST MONEY LAUNDERING (SCUML) /
        # Certificate of Registration". The bare acronym "scuml" carries the
        # same incidental-mention risk the "coren"/"corbon" lesson taught —
        # kept as a secondary pattern since no evidence of it appearing
        # incidentally elsewhere has turned up yet, but the full phrase is
        # the primary, safer match.
        "Special Control Unit Against Money Laundering (SCUML)",
        [
            "special control unit against money laundering",
            "scuml",
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
        # Checked before "Professional Registration" — a personnel-roster page
        # commonly mentions a regulatory body acronym (e.g. "(COREN)") inside a
        # qualifications table cell, which must not itself trigger
        # "Professional Registration" for what is really a CV/personnel-list
        # page. See the false positive found on the real 158-page bundle,
        # below.
        "Key Personnel CVs",
        [
            "curriculum vitae",
            "cv of ",
            # Confirmed against the real field-collected bundle: individual
            # CVs there have no "CURRICULUM VITAE" header at all (they open
            # directly with the person's name) — these two phrases are what
            # actually appears, on the roster page and each CV body respectively.
            "list of key personnel",
            "career objective",
            # Two more real formats found on two additional field-collected
            # bundles (Milestone 6 prep). Bare "key personnel" was tried and
            # rejected: it also appears incidentally inside an HSE
            # quality-policy page on the original bundle ("The key personnel
            # responsible for the implementation of the quality system...")
            # — same incidental-mention risk as elsewhere in this list.
            # These two are table/field-label phrases confirmed to appear
            # only on genuine personnel pages, never incidentally, across all
            # three real bundles on hand:
            "qualification | years of experience",  # roster-table format
            "position/function",  # numbered-field CV format
        ],
    ),
    (
        "Professional Registration",
        [
            "council for the regulation of engineering",
            # Bare acronyms ("coren", "corbon") were dropped: on the real
            # bundle, "(COREN)" appeared inside a Key Personnel qualifications
            # table cell — a mention, not a certificate — and mislabeled 16
            # pages of CVs as "Professional Registration" instead. Matched
            # against full institutional names instead, which only appear on
            # the actual certificate.
            "architects registration council of nigeria",
            "council of registered builders of nigeria",
            "professional registration",
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
            # "plant and equipment" was dropped (Milestone 6 prep, real-data
            # finding via expert ground-truth comparison): it's the standard
            # heading of a fixed-asset note inside ordinary audited financial
            # statements ("D. EXPLANATORY NOTES — Property, Plant and
            # Equipment"), not evidence of an actual equipment list. On a real
            # bundle this stole 3 financial-statement pages into "Equipment
            # Schedule" while the submission's real equipment evidence (an
            # equipment lease agreement) sat unclassified elsewhere — Cribra
            # then reported Non-Compliant on content the officer's own
            # ground-truth review confirmed was compliant. Real bundles show
            # the actual evidence is often an equipment *lease*, not a
            # literal schedule — these two phrases cover both orderings seen
            # ("EQUIPMENT LEASE" and "LEASE AGREEMENT FOR EQUIPMENT") and were
            # confirmed to appear only on genuine equipment-lease pages, never
            # incidentally, across all three real bundles on hand.
            "equipment lease",
            "lease agreement for equipment",
        ],
    ),
]


# Bare "contents" added (Milestone 6 prep, real-data validation on two
# additional field-collected bundles): several real TOC pages across both
# bundles headed themselves just "CONTENTS" or "CONTENTS PAGE(S)", not
# "table of contents". Without it, one such page's own line-item listing
# ("> LIST OF EQUIPMENTS") false-positive-matched Equipment Schedule and
# mislabeled the TOC page itself as that document. Checked for false
# positives across all three real bundles on hand: "contents" never appears
# outside a genuine TOC page in any of them.
_INDEX_PAGE_MARKERS = ("table of content", "table of contents", "contents")


def classify_page(text: str) -> str | None:
    """Return the matched document type label, or None if no header matched."""
    # Whitespace-normalized (newlines collapsed to single spaces) before
    # matching. False negative found on the real 158-page bundle: section-
    # divider pages ("EVIDENCE OF ITF\nCOMPLIANCE\nCERTIFICATE") lay a
    # multi-word phrase out across separate lines, so a plain substring match
    # against "itf compliance" never fired — the page returned None and
    # silently inherited whatever label came before it (the ITF divider was
    # absorbed into the preceding PENCOM segment instead of starting ITF).
    lowered = " ".join(text.lower().split())

    # False positive found on the real 158-page bundle: a table-of-contents
    # page lists every document type by name (often verbatim, e.g. "Tax
    # Clearance Certificate"), which used to keyword-match the first pattern
    # that happened to appear in list order — mislabeling the TOC itself as
    # that document. An index page is never itself a certificate/evidentiary
    # document, so bail out to Unclassified before checking any other pattern.
    if any(marker in lowered for marker in _INDEX_PAGE_MARKERS):
        return None

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
