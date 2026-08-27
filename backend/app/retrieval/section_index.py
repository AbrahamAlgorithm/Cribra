"""Structural marker detection for the requirement corpus: builds a
word-indexed reference list ("Public Procurement Act 2007, Section 4",
"BPP SBD (Works, Large Building), SECTION I: INSTRUCTIONS TO TENDERERS,
Clause 3.1") so each chunk produced by `chunker.chunk_text` can be tagged
with a human-checkable citation.

Implemented in Milestone 3, built from real inspection of the three actual
corpus documents rather than assumed formatting:

- PPA 2007 (PDF, genuine embedded text): sections are bare numbers at the
  start of a line — "2.  The Council shall", "3.—(1)  There is established"
  — never preceded by the word "Section" (that word only appears in
  cross-references like "Subject to sub-section (2) of this Section").
- BPP SBD (PDF, exported from Word — this matters: the original .docx used
  Word's automatic list-numbering for clause numbers like "3.11", which is
  *not* real text and can't be extracted by python-docx at all. Exporting to
  PDF flattens that auto-numbering into literal rendered text, which is why
  this corpus uses PDF exports instead of the original .docx files).
  Structure: "SECTION I: INSTRUCTIONS TO TENDERERS" (Section), "PART 1 -
  PROCEDURES" (Part), and clause numbers like "3.1" appearing alone on their
  own line, with the clause's title/body text on the following line(s).
- The Forms companion document uses "FORM: <NAME>" headers instead of
  numbered clauses.

Chunks before the first marker in a document (cover pages, tables of
contents) fall back to a page-number-only reference — every chunk gets a
citable reference, never `None`, matching the "requirement_source must be
populated on every result" hard requirement (SPEC.md Section 6) applied
here to the corpus side of grounding.
"""

from __future__ import annotations

import bisect
import re
from dataclasses import dataclass

# Real headers are ALL-CAPS ("PART 1 - PROCEDURES", "PART II—ESTABLISHMENT OF
# THE BUREAU OF PUBLIC PROCUREMENT"). Requiring that is a deliberate,
# evidence-based filter: a false positive was found where running prose
# *describing* the document's own structure ("this document includes...
# PART 1: Procedures Section I – Instructions...") got matched as a real
# Part header — that false case is title-case ("Procedures"), not all-caps.
_PART_PATTERN = re.compile(r"^PART\s+[IVXLCDM0-9]+\s*[—\-:]\s*([A-Z0-9][A-Z0-9 ,()&\-]+)$")
_SECTION_PATTERN = re.compile(r"^SECTION\s+[IVXLCDM]+\s*:\s*([A-Z0-9][A-Z0-9 ,()&\-]+)$")
_FORM_PATTERN = re.compile(r"^FORM\s*:\s*(.+)$", re.IGNORECASE)
# Standalone clause-number line, e.g. "3.1" on its own line (BPP SBD PDF export).
_CLAUSE_NUMBER_ONLY_PATTERN = re.compile(r"^(\d{1,2}\.\d{1,2})$")
# Bare section number starting a line, e.g. "2.  The Council shall" or
# "3.—(1)  There is established" (PPA 2007's actual drafting convention).
# Deliberately scoped to documents that opt in via `use_bare_number_sections`
# (see build_reference_index) rather than applied universally — a real false
# positive was found where this matched "17. The determination shall..." in
# the BPP SBD, which was actually a line-wrap of "under ITT 17." followed by
# an unrelated new sentence, not a section header at all.
_PPA_SECTION_PATTERN = re.compile(r"^(\d{1,3})\.(?:—|\s+)\S")

# Table-of-contents dot-leader line, e.g. "PART 1 - PROCEDURES.......5".
# Real bug found against the BPP SBD: without this, ToC entries got captured
# as literal section/part titles (dots and trailing page number included),
# and — worse — set `current_part`/`current_section` state prematurely, so
# every marker emitted afterward inherited garbled, concatenated text until
# the *real* (non-ToC) occurrence of that heading appeared later in the
# document. Same root cause as the table-of-contents false positive found in
# segmentation.py (Milestone 2) — a heading's text appearing in an index is
# not the same as the document actually being at that heading.
_TOC_DOT_LEADER_PATTERN = re.compile(r"\.{4,}")


@dataclass(frozen=True)
class ReferenceIndex:
    """Sorted (word_index, reference) pairs; `lookup` finds the reference
    active at a given word offset — i.e. the last marker at or before it."""

    _word_indices: list[int]
    _references: list[str]

    def lookup(self, word_index: int) -> str:
        position = bisect.bisect_right(self._word_indices, word_index) - 1
        if position < 0:
            return self._references[0] if self._references else ""
        return self._references[position]


def build_reference_index(
    pages: list[str], document_name: str, use_bare_number_sections: bool = False
) -> ReferenceIndex:
    """Scan a document's cleaned pages for structural markers.

    `pages` must be the same list (after preprocessing) whose `"\\n".join`
    is what gets passed to `chunker.chunk_text` — word counting here must
    stay aligned with that function's `text.split()` tokenization for
    `lookup(word_index)` to point at the right chunk.

    `use_bare_number_sections` opts into PPA 2007's "2.  The Council shall"
    drafting convention. Off by default — the BPP SBD has its own numbered
    references (e.g. "under ITT 17.") that collide with this pattern when
    applied universally; see `_PPA_SECTION_PATTERN`'s comment.
    """
    word_indices: list[int] = []
    references: list[str] = []

    current_part: str | None = None
    current_section: str | None = None
    word_count = 0

    def _emit(reference: str) -> None:
        word_indices.append(word_count)
        references.append(reference)

    # Every document gets a page-1 fallback reference at word 0, so text
    # before any structural marker (cover pages, tables of contents) is
    # still citable rather than falling back to an empty string.
    _emit(f"{document_name}, p. 1")

    for page_number, page_text in enumerate(pages, start=1):
        page_marker_emitted = False
        for line in page_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            # A dot-leader ToC line still contributes real words to the
            # document's token stream (chunker.chunk_text will tokenize it
            # too) — it must still be counted below, just never treated as
            # a marker or allowed to update current_part/current_section.
            is_toc_line = bool(_TOC_DOT_LEADER_PATTERN.search(stripped))

            part_match = None if is_toc_line else _PART_PATTERN.match(stripped)
            section_match = None if is_toc_line else _SECTION_PATTERN.match(stripped)
            form_match = None if is_toc_line else _FORM_PATTERN.match(stripped)
            clause_match = None if is_toc_line else _CLAUSE_NUMBER_ONLY_PATTERN.match(stripped)
            ppa_match = (
                None
                if is_toc_line or not use_bare_number_sections
                else _PPA_SECTION_PATTERN.match(stripped)
            )

            if part_match:
                current_part = stripped
                current_section = None
                _emit(f"{document_name}, {current_part}")
                page_marker_emitted = True
            elif section_match:
                current_section = stripped
                prefix = f"{current_part}, " if current_part else ""
                _emit(f"{document_name}, {prefix}{current_section}")
                page_marker_emitted = True
            elif form_match:
                _emit(f"{document_name}, {stripped}")
                page_marker_emitted = True
            elif clause_match:
                prefix_parts = [document_name]
                if current_part:
                    prefix_parts.append(current_part)
                if current_section:
                    prefix_parts.append(current_section)
                prefix_parts.append(f"Clause {clause_match.group(1)}")
                _emit(", ".join(prefix_parts))
                page_marker_emitted = True
            elif ppa_match:
                _emit(f"{document_name}, Section {ppa_match.group(1)}")
                page_marker_emitted = True
            elif not page_marker_emitted and word_count > 0:
                # First non-empty, non-matching line of a page with no
                # structural marker yet — still worth a page-level fallback
                # so a long gap between real markers doesn't leave chunks
                # citing a stale, much-earlier section.
                _emit(f"{document_name}, p. {page_number}")
                page_marker_emitted = True

            word_count += len(stripped.split())

    return ReferenceIndex(word_indices, references)
