"""Tests for bundle segmentation (Phase 2.1). Written in Milestone 2."""

from __future__ import annotations

from app.ingestion.segmentation import UNCLASSIFIED, classify_page, segment_document


def test_classify_page_matches_each_document_type():
    cases = {
        "CERTIFICATE OF INCORPORATION\nCorporate Affairs Commission\nRC Number: 123456": "CAC Certificate",
        "TAX CLEARANCE CERTIFICATE\nFederal Inland Revenue Service": "Tax Clearance Certificate",
        "NATIONAL PENSION COMMISSION\nCompliance Certificate": "PENCOM Compliance Certificate",
        "INDUSTRIAL TRAINING FUND\nITF Compliance Certificate": "ITF Compliance Certificate",
        "NIGERIA SOCIAL INSURANCE TRUST FUND\nNSITF": "NSITF Compliance Certificate",
        "AUDITED FINANCIAL STATEMENT\nIndependent Auditor's Report": "Audited Accounts",
        "COUNCIL FOR THE REGULATION OF ENGINEERING\nCOREN": "Professional Registration",
        "CURRICULUM VITAE\nJane Doe": "Key Personnel CVs",
        "AWARD LETTER\nCertificate of Completion": "Similar Project Experience",
        "EQUIPMENT SCHEDULE\nExcavator - owned": "Equipment Schedule",
    }
    for text, expected in cases.items():
        assert classify_page(text) == expected


def test_classify_page_matches_letter_of_award_phrasing():
    # Confirmed against a real field-collected bundle (SPEC.md Section 8,
    # Milestone 2 / phases.md Phase 2.1): the actual document uses "LETTER OF
    # AWARD", not the originally assumed "AWARD LETTER".
    assert classify_page("LETTER OF AWARD\nProject: Road Rehabilitation") == "Similar Project Experience"


def test_classify_page_returns_none_for_unrelated_text():
    assert classify_page("Dear Sir, please find attached our submission.") is None


def test_segment_document_groups_contiguous_pages_and_inherits_forward():
    pages = [
        "Dear Sir, please find attached our submission.",  # cover letter, unclassified
        "CERTIFICATE OF INCORPORATION\nRC Number: 123456",  # CAC page 1
        "...continued CAC details, no header repeated...",  # inherits CAC
        "TAX CLEARANCE CERTIFICATE\nFederal Inland Revenue Service",  # new segment
        "...continuation page with no header, e.g. a signature page...",  # inherits Tax Clearance
    ]

    segments = segment_document(pages, source_path="/tmp/bundle.pdf")

    # Only the leading run before any header is ever detected is "Unclassified" —
    # once a label is established, unheaded pages inherit it forward (per SPEC.md
    # Section 4.1a) until a *new* header is matched, however far that runs.
    assert len(segments) == 3
    assert segments[0].document_type == UNCLASSIFIED
    assert segments[0].page_start == 0 and segments[0].page_end == 0

    assert segments[1].document_type == "CAC Certificate"
    assert segments[1].page_start == 1 and segments[1].page_end == 2
    assert "continued CAC details" in segments[1].text

    assert segments[2].document_type == "Tax Clearance Certificate"
    assert segments[2].page_start == 3 and segments[2].page_end == 4
    assert "continuation page" in segments[2].text


def test_segment_document_leading_unclassified_run_stays_separate():
    pages = [
        "Cover letter with no recognizable header",
        "Another unrelated page, still no header",
        "EQUIPMENT SCHEDULE\nExcavator - owned",
    ]
    segments = segment_document(pages, source_path="/tmp/bundle.pdf")

    assert len(segments) == 2
    assert segments[0].document_type == UNCLASSIFIED
    assert segments[0].page_start == 0 and segments[0].page_end == 1
    assert segments[1].document_type == "Equipment Schedule"


def test_segment_document_empty_pages_returns_empty_list():
    assert segment_document([], source_path="/tmp/bundle.pdf") == []


def test_segment_document_single_type_bundle_is_one_segment():
    pages = [
        "EQUIPMENT SCHEDULE\nExcavator",
        "...page 2, no header...",
        "...page 3, no header...",
    ]
    segments = segment_document(pages, source_path="/tmp/bundle.pdf")
    assert len(segments) == 1
    assert segments[0].document_type == "Equipment Schedule"
    assert segments[0].page_start == 0 and segments[0].page_end == 2
