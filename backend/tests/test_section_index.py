"""Tests for requirement-corpus structural marker detection (Milestone 3).

Patterns and edge cases here are drawn from real inspection of the actual
PPA 2007 and BPP SBD corpus documents — see section_index.py's module
docstring for what each real document's structure actually looks like.
"""

from __future__ import annotations

from app.retrieval.section_index import ReferenceIndex, build_reference_index


def test_reference_index_lookup_before_first_marker_returns_first_reference():
    idx = ReferenceIndex([0, 100], ["doc, p. 1", "doc, Section 1"])
    assert idx.lookup(0) == "doc, p. 1"


def test_reference_index_lookup_between_markers_returns_nearest_preceding():
    idx = ReferenceIndex([0, 100, 250], ["doc, p. 1", "doc, Section 1", "doc, Section 2"])
    assert idx.lookup(150) == "doc, Section 1"
    assert idx.lookup(100) == "doc, Section 1"
    assert idx.lookup(99) == "doc, p. 1"


def test_reference_index_lookup_after_last_marker_returns_last_reference():
    idx = ReferenceIndex([0, 100], ["doc, p. 1", "doc, Section 1"])
    assert idx.lookup(10_000) == "doc, Section 1"


def test_build_reference_index_detects_ppa_style_bare_section_numbers():
    pages = [
        "PART II—ESTABLISHMENT OF THE BUREAU OF PUBLIC PROCUREMENT\n"
        "2.  The Council shall consider policies.\n"
        "3.—(1)  There is established an agency.\n"
        "4.  The objectives of the Bureau are set out below."
    ]
    idx = build_reference_index(pages, "Public Procurement Act 2007", use_bare_number_sections=True)
    references = idx._references
    assert any("PART II" in r for r in references)
    assert any("Section 2" in r for r in references)
    assert any("Section 3" in r for r in references)
    assert any("Section 4" in r for r in references)


def test_build_reference_index_ppa_pattern_not_applied_when_disabled():
    # This is the real false positive found on the BPP SBD: "under ITT 17."
    # line-wraps so "17." starts a new line, followed by an unrelated
    # sentence — must not be treated as a section header when
    # use_bare_number_sections=False (the default for non-PPA documents).
    pages = ["submitted by the Contractor, under ITT 17.\nThe determination shall not take this into account."]
    idx = build_reference_index(pages, "BPP SBD", use_bare_number_sections=False)
    assert not any("Section 17" in r for r in idx._references)


def test_build_reference_index_detects_bpp_sbd_structure():
    pages = [
        "PART 1 - PROCEDURES\n"
        "SECTION I: INSTRUCTIONS TO TENDERERS\n"
        "1.0\n"
        "Scope of tender\n"
        "1.1\n"
        "The Procuring Entity invites tenders."
    ]
    idx = build_reference_index(pages, "BPP SBD (Works, Large Building)")
    references = idx._references
    assert any("PART 1 - PROCEDURES" in r for r in references)
    assert any("SECTION I: INSTRUCTIONS TO TENDERERS" in r for r in references)
    assert any("Clause 1.0" in r for r in references)
    assert any("Clause 1.1" in r for r in references)
    # Clause references should carry the enclosing Part/Section forward.
    clause_ref = next(r for r in references if "Clause 1.1" in r)
    assert "PART 1 - PROCEDURES" in clause_ref
    assert "SECTION I: INSTRUCTIONS TO TENDERERS" in clause_ref


def test_build_reference_index_detects_form_headers():
    pages = ["FORM: FOREIGN CONTRACTORS 40% RULE\nPursuant to ITT 3.10, a foreign Contractor must complete this form."]
    idx = build_reference_index(pages, "BPP SBD Forms")
    assert any("FORM: FOREIGN CONTRACTORS 40% RULE" in r for r in idx._references)


def test_build_reference_index_ignores_table_of_contents_dot_leaders():
    # Real bug found on the BPP SBD: a ToC line like this used to be
    # captured as a literal (garbled) section title and corrupt all
    # subsequent markers via the current_part/current_section state.
    pages = [
        "PART 1 - PROCEDURES.......................................................................5\n"
        "SECTION I: INSTRUCTIONS TO TENDERERS................................................ 6\n"
        "PART 1 - PROCEDURES\n"
        "SECTION I: INSTRUCTIONS TO TENDERERS\n"
        "Real content follows here."
    ]
    idx = build_reference_index(pages, "BPP SBD")
    for ref in idx._references:
        assert "....." not in ref
        assert len(ref) < 150


def test_build_reference_index_rejects_mixed_case_prose_describing_structure():
    # Real false positive found on the BPP SBD: a sentence *describing* the
    # document's own structure ("PART 1: Procedures Section I – ...") got
    # matched as a real Part header. Genuine headers are ALL-CAPS
    # ("PART 1 - PROCEDURES"); this false case is title-case ("Procedures").
    pages = [
        "which includes all the sections specified below. "
        "PART 1: Procedures Section I – Instructions to Contractors "
        "PART 2: Requirements Section V – Schedule of Requirements"
    ]
    idx = build_reference_index(pages, "BPP SBD")
    assert not any("Procedures" in r and "PART 1 - " not in r for r in idx._references)


def test_build_reference_index_every_chunk_gets_a_citable_reference():
    # No chunk should ever resolve to an empty reference — matches the
    # domain model's "requirement_source must be populated on every result"
    # principle applied to the corpus side.
    pages = ["Some preamble text with no structural marker at all, e.g. a cover page."]
    idx = build_reference_index(pages, "Public Procurement Act 2007")
    assert idx.lookup(0) != ""
    assert "Public Procurement Act 2007" in idx.lookup(0)


def test_build_reference_index_counts_toc_line_words_to_avoid_offset_drift():
    # A skipped ToC line must still contribute to the word count — otherwise
    # every subsequent word_index would be out of sync with what
    # chunker.chunk_text actually tokenizes from the same joined text.
    pages = [
        "PART 1 - PROCEDURES.......................................................................5\n"
        "SECTION I: INSTRUCTIONS TO TENDERERS\n"
        "Real content."
    ]
    idx = build_reference_index(pages, "BPP SBD")
    full_text = "\n".join(pages)
    # The last marker's word_index must be <= the true total word count.
    assert idx._word_indices[-1] <= len(full_text.split())
