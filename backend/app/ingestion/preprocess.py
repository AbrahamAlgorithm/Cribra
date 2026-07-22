"""Text preprocessing: strip headers/footers/page numbers, normalise whitespace, dedupe.

Implemented in Milestone 2.
"""

from __future__ import annotations

import re

_PAGE_NUMBER_LINE = re.compile(r"^\s*(page\s+)?\d+(\s*(of|/)\s*\d+)?\s*$", re.IGNORECASE)
_WHITESPACE_RUN = re.compile(r"[ \t]+")
_BLANK_LINE_RUN = re.compile(r"\n{3,}")

# A line that repeats verbatim across at least this fraction of pages is
# almost certainly a running header/footer (letterhead, "Confidential", a
# repeated title), not content — strip it from every page.
_REPEATED_LINE_THRESHOLD = 0.5
_MIN_PAGES_FOR_REPEAT_DETECTION = 3


def normalize_whitespace(text: str) -> str:
    lines = [_WHITESPACE_RUN.sub(" ", line).strip() for line in text.splitlines()]
    collapsed = "\n".join(lines)
    return _BLANK_LINE_RUN.sub("\n\n", collapsed).strip()


def strip_page_numbers(text: str) -> str:
    lines = [line for line in text.splitlines() if not _PAGE_NUMBER_LINE.match(line)]
    return "\n".join(lines)


def _find_repeated_lines(pages: list[str]) -> set[str]:
    if len(pages) < _MIN_PAGES_FOR_REPEAT_DETECTION:
        return set()

    line_page_counts: dict[str, int] = {}
    for page in pages:
        seen_this_page = {line.strip() for line in page.splitlines() if line.strip()}
        for line in seen_this_page:
            line_page_counts[line] = line_page_counts.get(line, 0) + 1

    threshold = max(2, int(len(pages) * _REPEATED_LINE_THRESHOLD))
    return {line for line, count in line_page_counts.items() if count >= threshold}


def clean_pages(pages: list[str]) -> list[str]:
    """Strip page numbers, dedupe running headers/footers, normalise whitespace.

    Operates on the full page list at once because header/footer detection
    (unlike page-number stripping) requires cross-page context.
    """
    without_page_numbers = [strip_page_numbers(page) for page in pages]
    repeated_lines = _find_repeated_lines(without_page_numbers)

    deduped: list[str] = []
    for page in without_page_numbers:
        kept_lines = [line for line in page.splitlines() if line.strip() not in repeated_lines]
        deduped.append("\n".join(kept_lines))

    return [normalize_whitespace(page) for page in deduped]


def clean_text(text: str) -> str:
    """Single-document convenience wrapper (no cross-page dedupe context)."""
    return normalize_whitespace(strip_page_numbers(text))
