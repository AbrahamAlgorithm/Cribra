"""Per-requirement compliance evaluation and full-checklist orchestration.

Implemented in Milestones 4A/4B. Routes each `Requirement` to the
deterministic rule engine (4A, certificate types) or the RAG reasoning
engine (4B, evidentiary types) based on `segmentation.CERTIFICATE_DOCUMENT_TYPES`
— the same routing key Milestone 2 already established, since the default
checklist's requirement names are defined to match segmentation's document
type labels exactly.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date, datetime
from functools import partial
from typing import Literal

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from app.config import get_settings
from app.ingestion.schema import ExtractedDocument
from app.ingestion.segmentation import CERTIFICATE_DOCUMENT_TYPES
from app.models.domain import Requirement
from app.reasoning.prompt_templates import (
    REASONING_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    build_reasoning_user_message,
    build_report_user_message,
)
from app.reasoning.schema import ComplianceReport, ComplianceSummary, RequirementResult
from app.reasoning.validation_rules import validate_certificate
from app.retrieval.retriever import retrieve

logger = logging.getLogger(__name__)

MODEL = "gpt-4o"

# Rate limiting was a real, repeated finding in Milestone 2 (this account is
# capped at 30,000 TPM for gpt-4o) — max_retries is langchain_openai's own
# built-in backoff, set explicitly rather than trusting the library default.
_MAX_RETRIES = 6

# A single evidentiary segment's full text can alone exceed this account's
# 30,000 TPM cap once combined with retrieved source text and prompt
# overhead — confirmed on a real submission (Milestone 6 prep,
# Technical_Submission_2.pdf's Audited Accounts segment: ~28,600 tokens on
# its own, 46 pages), which failed outright with no retry able to help
# (max_retries backs off and repeats the *same* oversized request, which
# will never fit). Capped to the first ~12,500 tokens (rough 4-chars/token
# estimate for English prose — no tokenizer dependency in this codebase
# otherwise, and a rough cap with headroom is all that's needed here). Real
# bundles front-load the parts most relevant to a compliance judgment
# (corporate information, directors' report, independent auditor's report,
# statement of financial position) before the more voluminous notes/schedules.
_MAX_SUBMISSION_CONTENT_CHARS = 50_000

# 4A certificate checks are local/deterministic (no LLM call) so only the 4B
# evidentiary requirements actually hit OpenAI here — but each of those can
# carry up to ~12,500 tokens of submission content alone (see
# _MAX_SUBMISSION_CONTENT_CHARS above) plus retrieved source text, much
# heavier per call than a single vision transcription or field-extraction
# call. Kept well below page_resolver.py's concurrency of 5 to leave
# headroom under the same 30,000 TPM account cap — two full-sized calls
# concurrently already approaches the cap on their own. Threads, not
# asyncio, so evaluate_requirements' public signature stays plain sync;
# ChatOpenAI's own max_retries above is the safety net for any transient
# 429s a burst still triggers.
_MAX_CONCURRENT_EVALUATIONS = 3
_AUDITED_ACCOUNTS_REQUIREMENT_NAME = "Audited Accounts"
_AUDITED_STATEMENT_YEAR = re.compile(
    r"audited\s+financial\s+statements?\s+for\s+the\s+(?:year|period)\s+ended"
    r"[^0-9]{0,40}(?:31(?:st)?\s+dec(?:ember)?[,]?\s*|31/12/)?(?P<year>20\d{2})",
    re.IGNORECASE,
)
_ACCOUNT_STATEMENT_YEAR = re.compile(
    r"accounts?\s+for\s+the\s+(?:year|period)\s+ended"
    r"[^0-9]{0,40}(?:31(?:st)?\s+dec(?:ember)?[,]?\s*|31/12/)?(?P<year>20\d{2})",
    re.IGNORECASE,
)
_AUDITOR_REPORT_YEAR = re.compile(
    r"(?:independent\s+auditor(?:'s|s)?\s+report|auditor(?:'s|s)?\s+report|report\s+of\s+the\s+auditors?)"
    r"[^0-9]{0,120}(?:31(?:st)?\s+dec(?:ember)?[,]?\s*|31/12/)?(?P<year>20\d{2})",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _AuditedAccountsCoverage:
    target_years: tuple[int, ...]
    explicit_audited_years: frozenset[int]
    account_statement_years: frozenset[int]
    auditor_report_years: frozenset[int]

    @property
    def covered_years(self) -> tuple[int, ...]:
        covered = self.explicit_audited_years | (self.account_statement_years & self.auditor_report_years)
        return tuple(year for year in self.target_years if year in covered)

    @property
    def missing_years(self) -> tuple[int, ...]:
        covered = set(self.covered_years)
        return tuple(year for year in self.target_years if year not in covered)


class _ReasoningOutput(BaseModel):
    status: Literal["Compliant", "Non-Compliant", "Needs Review"]
    evidence_found: str | None = None
    justification: str
    confidence_note: str | None = None


class _ReportOutput(BaseModel):
    observations: list[str]
    overall_assessment: str


_llm: ChatOpenAI | None = None
_reasoning_llm = None
_report_llm = None


def _get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        settings = get_settings()
        _llm = ChatOpenAI(model=MODEL, temperature=0, api_key=settings.openai_api_key, max_retries=_MAX_RETRIES)
    return _llm


def _get_reasoning_llm():
    global _reasoning_llm
    if _reasoning_llm is None:
        _reasoning_llm = _get_llm().with_structured_output(_ReasoningOutput)
    return _reasoning_llm


def _get_report_llm():
    global _report_llm
    if _report_llm is None:
        _report_llm = _get_llm().with_structured_output(_ReportOutput)
    return _report_llm


def _normalize_for_pattern_matching(text: str) -> str:
    return " ".join(text.lower().split())


def _find_years(pattern: re.Pattern[str], text: str) -> frozenset[int]:
    return frozenset(int(match.group("year")) for match in pattern.finditer(text))


def _expected_previous_calendar_years(evaluation_date: date, count: int) -> tuple[int, ...]:
    start_year = evaluation_date.year - count
    return tuple(start_year + offset for offset in range(count))


def _detect_audited_accounts_coverage(text: str, evaluation_date: date) -> _AuditedAccountsCoverage:
    normalized = _normalize_for_pattern_matching(text)
    return _AuditedAccountsCoverage(
        target_years=_expected_previous_calendar_years(evaluation_date, 3),
        explicit_audited_years=_find_years(_AUDITED_STATEMENT_YEAR, normalized),
        account_statement_years=_find_years(_ACCOUNT_STATEMENT_YEAR, normalized),
        auditor_report_years=_find_years(_AUDITOR_REPORT_YEAR, normalized),
    )


def _format_years(years: tuple[int, ...] | frozenset[int]) -> str:
    ordered = sorted(years)
    if not ordered:
        return ""
    if len(ordered) == 1:
        return str(ordered[0])
    if len(ordered) == 2:
        return f"{ordered[0]} and {ordered[1]}"
    return f"{', '.join(str(year) for year in ordered[:-1])}, and {ordered[-1]}"


def _try_evaluate_audited_accounts(
    requirement: Requirement,
    submission_content: str | None,
    evaluation_date: date,
) -> RequirementResult | None:
    if requirement.name != _AUDITED_ACCOUNTS_REQUIREMENT_NAME or not submission_content:
        return None

    coverage = _detect_audited_accounts_coverage(submission_content, evaluation_date)
    if coverage.missing_years:
        return None

    years_text = _format_years(coverage.covered_years)
    return RequirementResult(
        requirement_id=requirement.id,
        requirement_name=requirement.name,
        status="Compliant",
        evidence_found=f"The submission includes audited financial statements for {years_text}.",
        requirement_source=requirement.source,
        justification=(
            f"The requirement specifies audited financial statements for the last 3 years. "
            f"As of the evaluation date ({evaluation_date.isoformat()}), that means "
            f"{years_text}. The submission text contains year-specific audited/accounts "
            f"statement headings and corresponding auditors' report language for each of those years."
        ),
        confidence_note=None,
    )


def _build_audited_accounts_pre_scan(coverage: _AuditedAccountsCoverage) -> str | None:
    findings: list[str] = []
    if coverage.explicit_audited_years:
        findings.append(f"explicit audited-statement headings: {_format_years(coverage.explicit_audited_years)}")
    if coverage.account_statement_years:
        findings.append(f"account-statement headings: {_format_years(coverage.account_statement_years)}")
    if coverage.auditor_report_years:
        findings.append(f"auditors' report references: {_format_years(coverage.auditor_report_years)}")

    if not findings:
        return None

    target_years = _format_years(coverage.target_years)
    return (
        "AUDITED ACCOUNTS PRE-SCAN:\n"
        f"Required years relative to the evaluation date: {target_years}.\n"
        f"Detected {'. '.join(findings)}."
    )


def evaluate_requirement(
    requirement: Requirement,
    extracted_documents: list[ExtractedDocument],
    evaluation_date: date,
) -> RequirementResult:
    """Evaluate one requirement — routes to 4A or 4B based on requirement type."""
    if requirement.name in CERTIFICATE_DOCUMENT_TYPES:
        return _evaluate_certificate_requirement(requirement, extracted_documents, evaluation_date)
    return _evaluate_evidentiary_requirement(requirement, extracted_documents, evaluation_date)


def _evaluate_certificate_requirement(
    requirement: Requirement,
    extracted_documents: list[ExtractedDocument],
    evaluation_date: date,
) -> RequirementResult:
    """4A: deterministic rule engine. No LLM, no retrieval."""
    matching = [d for d in extracted_documents if d.document_type == requirement.name]

    if not matching:
        return RequirementResult(
            requirement_id=requirement.id,
            requirement_name=requirement.name,
            status="Non-Compliant",
            evidence_found=None,
            requirement_source=requirement.source,
            justification="No matching certificate document was found in the submission.",
            confidence_note=None,
        )

    # A requirement type can legitimately match multiple segments (e.g. Tax
    # Clearance submitted for multiple years — confirmed on the real
    # 158-page submission). Every match is checked; the worst status wins,
    # since a real, evaluable problem with any one of them is worth
    # flagging rather than being masked by the others being fine.
    worst_status: Literal["Compliant", "Non-Compliant"] = "Compliant"
    justifications: list[str] = []
    evidence_bits: list[str] = []
    for document in matching:
        status, justification = validate_certificate(document, evaluation_date)
        justifications.append(justification)
        if document.holder_name:
            evidence_bits.append(
                f"{document.document_type} (pages {document.page_start}-{document.page_end}), "
                f"holder: {document.holder_name}"
            )
        if status == "Non-Compliant":
            worst_status = "Non-Compliant"

    # Real finding: two segments of the same certificate type that are both
    # simply valid (e.g. a certificate plus a supporting-document segment of
    # the same type) produce identical justification text — dedupe rather
    # than repeat the same sentence twice. dict.fromkeys preserves order.
    unique_justifications = list(dict.fromkeys(justifications))

    return RequirementResult(
        requirement_id=requirement.id,
        requirement_name=requirement.name,
        status=worst_status,
        evidence_found="; ".join(evidence_bits) or None,
        requirement_source=requirement.source,
        justification=" ".join(unique_justifications),
        confidence_note=None,
    )


def _evaluate_evidentiary_requirement(
    requirement: Requirement,
    extracted_documents: list[ExtractedDocument],
    evaluation_date: date,
) -> RequirementResult:
    """4B: RAG reasoning engine — retrieve grounding text, then a grounded LLM call."""
    matching = [d for d in extracted_documents if d.document_type == requirement.name]
    submission_content = "\n\n".join(d.normalized_text for d in matching if d.normalized_text) or None

    audited_accounts_result = _try_evaluate_audited_accounts(requirement, submission_content, evaluation_date)
    if audited_accounts_result is not None:
        return audited_accounts_result

    pre_scan = None
    if requirement.name == _AUDITED_ACCOUNTS_REQUIREMENT_NAME and submission_content:
        pre_scan = _build_audited_accounts_pre_scan(_detect_audited_accounts_coverage(submission_content, evaluation_date))

    submission_content_for_reasoning = submission_content
    if submission_content_for_reasoning and len(submission_content_for_reasoning) > _MAX_SUBMISSION_CONTENT_CHARS:
        logger.warning(
            "Truncating submission_content for requirement '%s' from %d to %d characters "
            "to stay under the OpenAI TPM limit.",
            requirement.name,
            len(submission_content_for_reasoning),
            _MAX_SUBMISSION_CONTENT_CHARS,
        )
        submission_content_for_reasoning = submission_content_for_reasoning[:_MAX_SUBMISSION_CONTENT_CHARS]

    if pre_scan and submission_content_for_reasoning:
        remaining_chars = max(0, _MAX_SUBMISSION_CONTENT_CHARS - len(pre_scan) - 2)
        submission_content_for_reasoning = f"{pre_scan}\n\n{submission_content_for_reasoning[:remaining_chars]}"
    elif pre_scan:
        submission_content_for_reasoning = pre_scan

    retrieved_chunks = retrieve(f"{requirement.name}: {requirement.description}", k=4)
    retrieved_text = (
        "\n\n".join(f"[{chunk.section_reference}]\n{chunk.text}" for chunk in retrieved_chunks)
        or "(no relevant source text retrieved)"
    )

    user_message = build_reasoning_user_message(
        requirement.name, requirement.description, retrieved_text, submission_content_for_reasoning, evaluation_date
    )

    output: _ReasoningOutput = _get_reasoning_llm().invoke(
        [
            {"role": "system", "content": REASONING_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]
    )

    return RequirementResult(
        requirement_id=requirement.id,
        requirement_name=requirement.name,
        status=output.status,
        evidence_found=output.evidence_found,
        requirement_source=requirement.source,
        justification=output.justification,
        confidence_note=output.confidence_note,
    )


def evaluate_requirements(
    requirements: list[Requirement],
    extracted_documents: list[ExtractedDocument],
    evaluation_date: date,
) -> list[RequirementResult]:
    """4A/4B across a full checklist — the per-requirement evaluation phase.

    Split out from `evaluate_submission` in Milestone 5 so `routes_evaluate.py`
    can report `Evaluation.status = "evaluating"` around just this phase and
    `"generating_report"` around `build_report` below, rather than the two
    being invisibly bundled into one opaque call.

    Run concurrently (Milestone 6 prep — real-data validation found this
    phase was the dominant cost in a 3+ minute evaluation, entirely from
    running independent 4B reasoning calls one at a time). Each requirement
    is evaluated independently of the others, so there's no ordering
    dependency between them; ThreadPoolExecutor.map preserves the input
    order in the returned list regardless.
    """
    evaluate_one = partial(evaluate_requirement, extracted_documents=extracted_documents, evaluation_date=evaluation_date)
    with ThreadPoolExecutor(max_workers=_MAX_CONCURRENT_EVALUATIONS) as pool:
        return list(pool.map(evaluate_one, requirements))


def build_report(evaluation_id: str, results: list[RequirementResult]) -> ComplianceReport:
    """Assemble `ComplianceSummary` and generate observations/overall_assessment."""
    compliant = sum(1 for r in results if r.status == "Compliant")
    non_compliant = sum(1 for r in results if r.status == "Non-Compliant")
    needs_review = sum(1 for r in results if r.status == "Needs Review")
    total = len(results)
    compliance_score = round((compliant / total) * 100, 1) if total else 0.0

    summary = ComplianceSummary(
        requirements_evaluated=total,
        compliant=compliant,
        non_compliant=non_compliant,
        needs_review=needs_review,
        compliance_score=compliance_score,
    )

    observations, overall_assessment = _generate_report_narrative(results, summary)

    return ComplianceReport(
        evaluation_id=evaluation_id,
        generated_at=datetime.now(),
        results=results,
        summary=summary,
        observations=observations,
        overall_assessment=overall_assessment,
    )


def evaluate_submission(
    evaluation_id: str,
    requirements: list[Requirement],
    extracted_documents: list[ExtractedDocument],
    evaluation_date: date,
) -> ComplianceReport:
    """Convenience wrapper: evaluate_requirements + build_report in one call."""
    results = evaluate_requirements(requirements, extracted_documents, evaluation_date)
    return build_report(evaluation_id, results)


def _generate_report_narrative(
    results: list[RequirementResult], summary: ComplianceSummary
) -> tuple[list[str], str]:
    results_summary = "\n".join(f"- {r.requirement_name}: {r.status} — {r.justification}" for r in results)
    results_summary += (
        f"\n\nSummary: {summary.compliant}/{summary.requirements_evaluated} compliant, "
        f"{summary.non_compliant} non-compliant, {summary.needs_review} needs review."
    )

    output: _ReportOutput = _get_report_llm().invoke(
        [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": build_report_user_message(results_summary)},
        ]
    )
    return output.observations, output.overall_assessment
