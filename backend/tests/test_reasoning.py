"""Tests for the reasoning layer: validation_rules.py (4A) and evaluator.py
(4A/4B routing + full-checklist orchestration). Written in Milestone 4.

LLM calls and retrieval are mocked throughout — no real OpenAI/ChromaDB
calls in the automated suite. Real end-to-end validation against the real
158-page submission + default checklist is verified separately (see the
Milestone 4 update doc).
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace

from app.ingestion.schema import ExtractedDocument
from app.models.domain import Requirement, RequirementSource
from app.reasoning import evaluator
from app.reasoning.schema import ComplianceReport
from app.reasoning.validation_rules import validate_certificate


def _make_requirement(name: str, description: str = "", source_type: str = "default") -> Requirement:
    return Requirement(
        id=f"req-{name}",
        name=name,
        description=description,
        is_mandatory=True,
        source=RequirementSource(type=source_type, document_name="Test Doc", section_reference=None),
    )


def _make_extracted_document(document_type: str, **kwargs) -> ExtractedDocument:
    defaults = dict(
        extraction_method="text",
        holder_name="Example Contractors Ltd",
        identifier="RC1234567",
        issue_date=date(2020, 1, 1),
        expiry_date=None,
        normalized_text=None,
        page_start=0,
        page_end=0,
        source_path="/tmp/bundle.pdf",
    )
    defaults.update(kwargs)
    return ExtractedDocument(document_type=document_type, **defaults)


# --- validate_certificate (4A) ------------------------------------------------


def test_validate_certificate_compliant_when_not_expired():
    doc = _make_extracted_document("CAC Certificate", expiry_date=None)
    status, _ = validate_certificate(doc, date(2026, 1, 1))
    assert status == "Compliant"


def test_validate_certificate_non_compliant_when_expired():
    doc = _make_extracted_document("Tax Clearance Certificate", expiry_date=date(2025, 1, 1))
    status, justification = validate_certificate(doc, date(2026, 1, 1))
    assert status == "Non-Compliant"
    assert "expired" in justification.lower()


def test_validate_certificate_compliant_on_exact_evaluation_date():
    # "earlier than" (strict) per SPEC.md Section 4.3 — expiring *on* the
    # evaluation date is not yet expired.
    doc = _make_extracted_document("ITF Compliance Certificate", expiry_date=date(2026, 1, 1))
    status, _ = validate_certificate(doc, date(2026, 1, 1))
    assert status == "Compliant"


def test_validate_certificate_non_compliant_when_fields_missing():
    doc = _make_extracted_document("PENCOM Compliance Certificate", holder_name=None, identifier=None)
    status, justification = validate_certificate(doc, date(2026, 1, 1))
    assert status == "Non-Compliant"
    assert "missing evidence" in justification.lower()


# --- evaluate_requirement routing ---------------------------------------------


def test_evaluate_requirement_routes_certificate_types_to_4a(monkeypatch):
    called = {"4a": False, "4b": False}
    monkeypatch.setattr(
        evaluator, "_evaluate_certificate_requirement", lambda *a: called.__setitem__("4a", True) or "result"
    )
    monkeypatch.setattr(
        evaluator, "_evaluate_evidentiary_requirement", lambda *a: called.__setitem__("4b", True) or "result"
    )

    requirement = _make_requirement("CAC Certificate")
    evaluator.evaluate_requirement(requirement, [], date(2026, 1, 1))

    assert called["4a"] is True
    assert called["4b"] is False


def test_evaluate_requirement_routes_evidentiary_types_to_4b(monkeypatch):
    called = {"4a": False, "4b": False}
    monkeypatch.setattr(
        evaluator, "_evaluate_certificate_requirement", lambda *a: called.__setitem__("4a", True) or "result"
    )
    monkeypatch.setattr(
        evaluator, "_evaluate_evidentiary_requirement", lambda *a: called.__setitem__("4b", True) or "result"
    )

    requirement = _make_requirement("Similar Project Experience")
    evaluator.evaluate_requirement(requirement, [], date(2026, 1, 1))

    assert called["4b"] is True
    assert called["4a"] is False


# --- _evaluate_certificate_requirement (4A) ------------------------------------


def test_certificate_requirement_non_compliant_when_no_matching_document():
    requirement = _make_requirement("CAC Certificate")
    result = evaluator._evaluate_certificate_requirement(requirement, [], date(2026, 1, 1))

    assert result.status == "Non-Compliant"
    assert result.requirement_source == requirement.source
    assert "no matching" in result.justification.lower()


def test_certificate_requirement_compliant_when_document_valid():
    requirement = _make_requirement("CAC Certificate")
    document = _make_extracted_document("CAC Certificate")
    result = evaluator._evaluate_certificate_requirement(requirement, [document], date(2026, 1, 1))

    assert result.status == "Compliant"
    assert result.requirement_id == requirement.id
    assert result.requirement_source == requirement.source


def test_certificate_requirement_worst_status_wins_across_multiple_documents():
    # Real scenario confirmed on the field-collected submission: the same
    # certificate type can legitimately appear as multiple segments.
    requirement = _make_requirement("Tax Clearance Certificate")
    valid_doc = _make_extracted_document("Tax Clearance Certificate", expiry_date=date(2027, 1, 1))
    expired_doc = _make_extracted_document("Tax Clearance Certificate", expiry_date=date(2020, 1, 1))
    result = evaluator._evaluate_certificate_requirement(requirement, [valid_doc, expired_doc], date(2026, 1, 1))
    assert result.status == "Non-Compliant"


def test_certificate_requirement_dedupes_identical_justifications():
    # Real bug found on the 158-page submission: CAC Certificate matched two
    # segments (the certificate itself plus a supporting-document segment of
    # the same type), both simply valid — the justification was the same
    # sentence repeated twice ("...is present and valid... ...is present and
    # valid...") before this fix.
    requirement = _make_requirement("CAC Certificate")
    doc_a = _make_extracted_document("CAC Certificate", page_start=3, page_end=13)
    doc_b = _make_extracted_document("CAC Certificate", page_start=68, page_end=91)
    result = evaluator._evaluate_certificate_requirement(requirement, [doc_a, doc_b], date(2026, 1, 1))

    assert result.status == "Compliant"
    assert result.justification.count("is present and valid") == 1


# --- _evaluate_evidentiary_requirement (4B) ------------------------------------


class _FakeLLM:
    def __init__(self, output):
        self.output = output
        self.invoked_with = None

    def invoke(self, messages):
        self.invoked_with = messages
        return self.output


def test_evidentiary_requirement_maps_llm_output_correctly(monkeypatch):
    fake_output = evaluator._ReasoningOutput(
        status="Compliant",
        evidence_found="3 completed projects with award letters.",
        justification="Matches the retrieved requirement text citing 3-5 completed jobs.",
        confidence_note=None,
    )
    fake_llm = _FakeLLM(fake_output)
    monkeypatch.setattr(evaluator, "_get_reasoning_llm", lambda: fake_llm)
    monkeypatch.setattr(
        evaluator,
        "retrieve",
        lambda query, k=4: [
            SimpleNamespace(text="Contractors must show 3-5 similar jobs.", section_reference="BPP SBD, Clause 5")
        ],
    )

    requirement = _make_requirement("Similar Project Experience", "3-5 completed jobs")
    document = _make_extracted_document(
        "Similar Project Experience", normalized_text="Project A, Project B, Project C completion certs."
    )
    result = evaluator._evaluate_evidentiary_requirement(requirement, [document], date(2026, 8, 25))

    assert result.status == "Compliant"
    assert result.evidence_found == fake_output.evidence_found
    assert result.requirement_source == requirement.source
    assert "Project A" in fake_llm.invoked_with[1]["content"]
    assert "BPP SBD, Clause 5" in fake_llm.invoked_with[1]["content"]
    assert "2026-08-25" in fake_llm.invoked_with[1]["content"]


def test_evidentiary_requirement_handles_no_submission_content(monkeypatch):
    fake_output = evaluator._ReasoningOutput(
        status="Non-Compliant", evidence_found=None, justification="No evidence found.", confidence_note=None
    )
    fake_llm = _FakeLLM(fake_output)
    monkeypatch.setattr(evaluator, "_get_reasoning_llm", lambda: fake_llm)
    monkeypatch.setattr(evaluator, "retrieve", lambda query, k=4: [])

    requirement = _make_requirement("Equipment Schedule")
    result = evaluator._evaluate_evidentiary_requirement(requirement, [], date(2026, 8, 25))

    assert result.status == "Non-Compliant"
    assert "no matching content found" in fake_llm.invoked_with[1]["content"].lower()


def test_evidentiary_requirement_truncates_oversized_submission_content(monkeypatch):
    # Real finding (Milestone 6 prep): a real 46-page Audited Accounts segment
    # alone requested ~30,491 tokens against this account's 30,000 TPM cap and
    # failed outright — no retry can help, since it's the same oversized
    # request every time. `_evaluate_evidentiary_requirement` must cap the
    # submission content it sends, not just pass the whole segment through.
    fake_output = evaluator._ReasoningOutput(
        status="Compliant", evidence_found="Present.", justification="ok", confidence_note=None
    )
    fake_llm = _FakeLLM(fake_output)
    monkeypatch.setattr(evaluator, "_get_reasoning_llm", lambda: fake_llm)
    monkeypatch.setattr(evaluator, "retrieve", lambda query, k=4: [])

    oversized_text = "x" * (evaluator._MAX_SUBMISSION_CONTENT_CHARS + 10_000)
    requirement = _make_requirement("Audited Accounts")
    document = _make_extracted_document("Audited Accounts", normalized_text=oversized_text)
    evaluator._evaluate_evidentiary_requirement(requirement, [document], date(2026, 8, 25))

    sent_content = fake_llm.invoked_with[1]["content"]
    assert ("x" * evaluator._MAX_SUBMISSION_CONTENT_CHARS) in sent_content
    assert ("x" * (evaluator._MAX_SUBMISSION_CONTENT_CHARS + 1)) not in sent_content


def test_detect_audited_accounts_coverage_ignores_comparative_year_columns():
    text = """
    Audited Financial Statements For The Year Ended 31/12/2023
    Report of the Auditors to the Members for the period ended 31st December, 2023
    STATEMENT OF PROFIT AND LOSS
    NOTE 2023 2022
    Earnings 52,715,038 20,079,144
    """

    coverage = evaluator._detect_audited_accounts_coverage(text, date(2026, 8, 25))

    assert coverage.target_years == (2023, 2024, 2025)
    assert coverage.explicit_audited_years == frozenset({2023})
    assert coverage.auditor_report_years == frozenset({2023})
    assert coverage.covered_years == (2023,)
    assert coverage.missing_years == (2024, 2025)


def test_audited_accounts_requirement_short_circuits_when_all_three_years_detected(monkeypatch):
    monkeypatch.setattr(evaluator, "_get_reasoning_llm", lambda: pytest.fail("LLM should not run for this case."))
    monkeypatch.setattr(evaluator, "retrieve", lambda *a, **k: pytest.fail("Retriever should not run for this case."))

    requirement = _make_requirement("Audited Accounts", "Audited financial statements for the last 3 years.")
    document = _make_extracted_document(
        "Audited Accounts",
        normalized_text="""
        Audited Financial Statements For The Year Ended 31/12/2023
        Report of the Auditors to the Members for the period ended 31st December, 2023
        Accounts for the Period Ended 31st December, 2024
        Auditors Report for the Period Ended 31st December, 2024
        Accounts for the Period Ended 31st December, 2025
        Auditors Report for the Period Ended 31st December, 2025
        """,
    )

    result = evaluator._evaluate_evidentiary_requirement(requirement, [document], date(2026, 8, 25))

    assert result.status == "Compliant"
    assert "2023, 2024, and 2025" in result.evidence_found
    assert "2023, 2024, and 2025" in result.justification


def test_audited_accounts_pre_scan_is_passed_to_reasoning_when_years_are_incomplete(monkeypatch):
    fake_output = evaluator._ReasoningOutput(
        status="Needs Review",
        evidence_found="Only two audited years detected.",
        justification="Missing one required year.",
        confidence_note="2025 was not found.",
    )
    fake_llm = _FakeLLM(fake_output)
    monkeypatch.setattr(evaluator, "_get_reasoning_llm", lambda: fake_llm)
    monkeypatch.setattr(evaluator, "retrieve", lambda query, k=4: [])

    requirement = _make_requirement("Audited Accounts", "Audited financial statements for the last 3 years.")
    document = _make_extracted_document(
        "Audited Accounts",
        normalized_text="""
        Audited Financial Statements For The Year Ended 31/12/2023
        Report of the Auditors to the Members for the period ended 31st December, 2023
        Accounts for the Period Ended 31st December, 2024
        Auditors Report for the Period Ended 31st December, 2024
        """,
    )

    evaluator._evaluate_evidentiary_requirement(requirement, [document], date(2026, 8, 25))

    sent_content = fake_llm.invoked_with[1]["content"]
    assert "AUDITED ACCOUNTS PRE-SCAN:" in sent_content
    assert "Required years relative to the evaluation date: 2023, 2024, and 2025." in sent_content
    assert "account-statement headings: 2024" in sent_content


# --- evaluate_submission (full orchestration) ----------------------------------


def test_evaluate_submission_assembles_correct_summary_and_report(monkeypatch):
    requirements = [_make_requirement("CAC Certificate"), _make_requirement("Similar Project Experience")]
    documents = [_make_extracted_document("CAC Certificate")]

    monkeypatch.setattr(
        evaluator,
        "_evaluate_evidentiary_requirement",
        lambda req, docs, eval_date: evaluator.RequirementResult(
            requirement_id=req.id,
            requirement_name=req.name,
            status="Needs Review",
            evidence_found=None,
            requirement_source=req.source,
            justification="Ambiguous.",
            confidence_note="Not enough detail.",
        ),
    )

    fake_report_output = evaluator._ReportOutput(
        observations=["One requirement needs review."],
        overall_assessment="1 of 2 requirements compliant; 1 needs human verification.",
    )
    monkeypatch.setattr(evaluator, "_get_report_llm", lambda: _FakeLLM(fake_report_output))

    report = evaluator.evaluate_submission("eval-1", requirements, documents, date(2026, 1, 1))

    assert isinstance(report, ComplianceReport)
    assert report.evaluation_id == "eval-1"
    assert report.summary.requirements_evaluated == 2
    assert report.summary.compliant == 1
    assert report.summary.needs_review == 1
    assert report.summary.compliance_score == 50.0
    assert report.observations == fake_report_output.observations
    assert report.overall_assessment == fake_report_output.overall_assessment
    assert len(report.results) == 2
