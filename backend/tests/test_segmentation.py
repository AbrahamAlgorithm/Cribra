"""Tests for bundle segmentation (Phase 2.1). Written in Milestone 2."""

from __future__ import annotations

from app.ingestion.segmentation import NON_CHECKLIST_DOCUMENT_TYPES, UNCLASSIFIED, classify_page, segment_document


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


def test_classify_page_matches_pension_compliance_divider_phrasing():
    # Confirmed against the real bundle: the PENCOM section-divider page says
    # "EVIDENCE OF PENSION COMPLIANCE CERTIFICATE" (compliance, not
    # commission) — without this pattern, the divider silently inherited
    # whatever segment preceded it instead of joining PENCOM.
    assert classify_page("EVIDENCE OF PENSION\nCOMPLIANCE\nCERTIFICATE") == "PENCOM Compliance Certificate"


def test_classify_page_bpp_compliance_table_not_misread_as_pencom():
    # Real false positive found on the 158-page bundle: the BPP Interim
    # Registration Report's own compliance-summary table has "PENCOM" as a
    # column header ("Compliant with 3 personnel, as obtained from PENCOM"),
    # which used to misclassify the IRR certificate's own page as PENCOM
    # (bare "pencom" acronym matching was too loose, same lesson as coren/corbon).
    irr_page_with_compliance_table = (
        "BUREAU OF PUBLIC PROCUREMENT\n"
        "Interim Registration Report (IRR)\n\n"
        "FIRS | PENCOM | NSITF | ITF\n"
        "Compliant | Compliant with 3 personnel, as obtained from PENCOM | Compliant | Compliant"
    )
    assert classify_page(irr_page_with_compliance_table) == "Interim Registration Report (BPP)"


def test_classify_page_matches_interim_registration_report_bpp():
    # Confirmed real phrasing on both the divider and the actual certificate.
    assert classify_page("EVIDENCE OF\nREGISTRATION WITH\nBPP") == "Interim Registration Report (BPP)"
    assert (
        classify_page("BUREAU OF PUBLIC PROCUREMENT\nInterim Registration Report (IRR)")
        == "Interim Registration Report (BPP)"
    )
    assert "Interim Registration Report (BPP)" in NON_CHECKLIST_DOCUMENT_TYPES


def test_classify_page_matches_scuml_certificate():
    # Real document type found in the bundle that isn't mentioned anywhere in
    # the bundle's own table of contents — a genuine "extra" document, not an
    # omission. Must be recognized and correctly isolated, not swallowed into
    # whatever certificate segment precedes it.
    scuml_text = (
        "SPECIAL CONTROL UNIT AGAINST MONEY LAUNDERING\n(SCUML)\n\nCertificate of Registration"
    )
    assert classify_page(scuml_text) == "Special Control Unit Against Money Laundering (SCUML)"
    assert "Special Control Unit Against Money Laundering (SCUML)" in NON_CHECKLIST_DOCUMENT_TYPES


def test_classify_page_matches_letter_of_award_phrasing():
    # Confirmed against a real field-collected bundle (SPEC.md Section 8,
    # Milestone 2 / phases.md Phase 2.1): the actual document uses "LETTER OF
    # AWARD", not the originally assumed "AWARD LETTER".
    assert classify_page("LETTER OF AWARD\nProject: Road Rehabilitation") == "Similar Project Experience"


def test_classify_page_key_personnel_roster_not_misread_as_professional_registration():
    # Real false positive found on the 158-page field-collected bundle: a
    # "LIST OF KEY PERSONNEL" roster table mentions "(COREN)" inside a
    # qualifications cell, which used to trigger "Professional Registration"
    # for what is actually the opening page of a 16-page CV/personnel section
    # (bare "coren"/"corbon" acronym matching was too loose). Must classify
    # as "Key Personnel CVs" instead.
    roster_page = (
        "LIST OF KEY PERSONNEL\n"
        "| S/N | NAME | QUALIFICATION | YEARS OF EXPERIENCE |\n"
        "| 1. | Jane Doe | Civil Engineer (B.Sc), (COREN) | 17 yrs |"
    )
    assert classify_page(roster_page) == "Key Personnel CVs"


def test_classify_page_cv_body_without_curriculum_vitae_header():
    # The real bundle's individual CVs open directly with the person's name —
    # no "CURRICULUM VITAE" header — but do use "CAREER OBJECTIVE".
    cv_body = "JOHN DOE\n\nCAREER OBJECTIVE:\n\nTo contribute the best of my ability..."
    assert classify_page(cv_body) == "Key Personnel CVs"


def test_classify_page_matches_full_institutional_names_for_professional_registration():
    # Full institutional names, confirmed against a real certificate in the
    # field-collected bundle — more specific than a bare acronym, so a mere
    # mention elsewhere (e.g. in a CV) can't false-positive on these.
    assert (
        classify_page("ARCHITECTS REGISTRATION COUNCIL OF NIGERIA\nTHIS IS TO CERTIFY THAT...")
        == "Professional Registration"
    )
    assert (
        classify_page("COUNCIL OF REGISTERED BUILDERS OF NIGERIA\nCertificate of Registration")
        == "Professional Registration"
    )


def test_classify_page_returns_none_for_unrelated_text():
    assert classify_page("Dear Sir, please find attached our submission.") is None


def test_classify_page_matches_phrase_split_across_lines():
    # Real false negative found on the 158-page field-collected bundle: a
    # section-divider page renders "EVIDENCE OF ITF\nCOMPLIANCE\nCERTIFICATE"
    # (each word/phrase on its own line, from the vision transcription's
    # layout). A plain substring match against "itf compliance" never fired,
    # so the page returned None and silently inherited the *previous*
    # segment's label instead of starting its own ITF segment.
    divider_page = "EVIDENCE OF ITF\nCOMPLIANCE\nCERTIFICATE\n\nCORPORATE PROFILE"
    assert classify_page(divider_page) == "ITF Compliance Certificate"


def test_classify_page_table_of_contents_is_never_classified_as_a_document():
    # Real false positive found on the 158-page field-collected bundle: a
    # table-of-contents page lists every document type by name verbatim
    # (including "Tax Clearance Certificate"), which used to get keyword-
    # matched as if the TOC page itself were that certificate. An index page
    # must always classify as None (Unclassified), regardless of which
    # document names it happens to list.
    toc_page = (
        "TABLE OF CONTENT\n\n"
        "1. Certification of Incorporate, Including MEMART, CAC2, CAC7\n"
        "2. Tax Clearance Certificate\n"
        "3. Pension Compliance Certificate\n"
        "10. List of Equipment"
    )
    assert classify_page(toc_page) is None


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
