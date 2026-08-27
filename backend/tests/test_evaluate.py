"""Tests for POST /api/evaluate, GET /api/status/{id}, GET /api/reports/{id}.

Milestone 5. The heavy pipeline steps (`process_document`,
`evaluate_requirements`, `build_report`) are mocked — no real extraction or
LLM calls in the automated suite. FastAPI's TestClient runs background
tasks to completion before returning control, so these tests don't need to
poll — the background task has already finished by the time each
`client.post`/`client.get` call returns.
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from app.api import routes_evaluate
from app.main import app
from app.reasoning.schema import ComplianceReport, ComplianceSummary, RequirementResult

client = None  # set in fixture


@pytest.fixture(autouse=True)
def _client():
    global client
    from fastapi.testclient import TestClient

    client = TestClient(app)
    yield client


def _create_evaluation_with_submission() -> str:
    evaluation = client.post("/api/requirements", json={"mode": "default"}).json()
    evaluation_id = evaluation["id"]
    client.post(
        "/api/submissions",
        data={"evaluation_id": evaluation_id},
        files=[("files", ("cac.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    return evaluation_id


def _fake_report(evaluation_id: str) -> ComplianceReport:
    return ComplianceReport(
        evaluation_id=evaluation_id,
        generated_at=datetime.now(),
        results=[
            RequirementResult(
                requirement_id="req-1",
                requirement_name="CAC Certificate",
                status="Compliant",
                evidence_found="Present",
                requirement_source={"type": "default", "document_name": "Default Checklist", "section_reference": None},
                justification="Valid.",
                confidence_note=None,
            )
        ],
        summary=ComplianceSummary(requirements_evaluated=1, compliant=1, non_compliant=0, needs_review=0, compliance_score=100.0),
        observations=["All requirements satisfied."],
        overall_assessment="1 of 1 requirements compliant. This report is intended to support, not replace, professional evaluation.",
    )


# --- POST /api/evaluate: success path -----------------------------------------


def test_evaluate_full_success_flow(monkeypatch):
    evaluation_id = _create_evaluation_with_submission()

    monkeypatch.setattr(routes_evaluate, "process_document", lambda path: [])
    monkeypatch.setattr(routes_evaluate, "evaluate_requirements", lambda reqs, docs, d: [])
    monkeypatch.setattr(routes_evaluate, "build_report", lambda eid, results: _fake_report(eid))

    response = client.post("/api/evaluate", json={"evaluation_id": evaluation_id})
    assert response.status_code == 202
    assert response.json()["id"] == evaluation_id

    status_response = client.get(f"/api/status/{evaluation_id}")
    assert status_response.status_code == 200
    assert status_response.json() == {"evaluation_id": evaluation_id, "status": "complete"}

    report_response = client.get(f"/api/reports/{evaluation_id}")
    assert report_response.status_code == 200
    body = report_response.json()
    assert body["evaluation_id"] == evaluation_id
    assert body["summary"]["compliant"] == 1
    assert "support, not replace" in body["overall_assessment"]


def test_evaluate_calls_process_document_per_submission_file(monkeypatch):
    evaluation_id = _create_evaluation_with_submission()

    calls = []
    monkeypatch.setattr(routes_evaluate, "process_document", lambda path: calls.append(path) or [])
    monkeypatch.setattr(routes_evaluate, "evaluate_requirements", lambda reqs, docs, d: [])
    monkeypatch.setattr(routes_evaluate, "build_report", lambda eid, results: _fake_report(eid))

    client.post("/api/evaluate", json={"evaluation_id": evaluation_id})

    assert len(calls) == 1  # one file was uploaded in _create_evaluation_with_submission


# --- POST /api/evaluate: error paths -------------------------------------------


def test_evaluate_rejects_unknown_evaluation():
    response = client.post("/api/evaluate", json={"evaluation_id": "does-not-exist"})
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_evaluate_rejects_evaluation_without_submission():
    evaluation = client.post("/api/requirements", json={"mode": "default"}).json()

    response = client.post("/api/evaluate", json={"evaluation_id": evaluation["id"]})
    assert response.status_code == 400
    assert response.json()["error"] == "bad_request"


def test_evaluate_rejects_evaluation_not_pending(monkeypatch):
    evaluation_id = _create_evaluation_with_submission()
    monkeypatch.setattr(routes_evaluate, "process_document", lambda path: [])
    monkeypatch.setattr(routes_evaluate, "evaluate_requirements", lambda reqs, docs, d: [])
    monkeypatch.setattr(routes_evaluate, "build_report", lambda eid, results: _fake_report(eid))

    first = client.post("/api/evaluate", json={"evaluation_id": evaluation_id})
    assert first.status_code == 202

    second = client.post("/api/evaluate", json={"evaluation_id": evaluation_id})
    assert second.status_code == 409
    assert second.json()["error"] == "conflict"


# --- POST /api/evaluate: failure path (pipeline raises) -----------------------


def test_evaluate_failure_marks_evaluation_failed(monkeypatch):
    evaluation_id = _create_evaluation_with_submission()

    def _boom(path):
        raise ValueError("simulated extraction failure")

    monkeypatch.setattr(routes_evaluate, "process_document", _boom)

    client.post("/api/evaluate", json={"evaluation_id": evaluation_id})

    status_response = client.get(f"/api/status/{evaluation_id}")
    assert status_response.json()["status"] == "failed"

    report_response = client.get(f"/api/reports/{evaluation_id}")
    assert report_response.status_code == 409
    assert report_response.json()["error"] == "conflict"


# --- GET /api/status ------------------------------------------------------------


def test_status_rejects_unknown_evaluation():
    response = client.get("/api/status/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_status_returns_pending_before_evaluate_is_called():
    evaluation_id = _create_evaluation_with_submission()
    response = client.get(f"/api/status/{evaluation_id}")
    assert response.json() == {"evaluation_id": evaluation_id, "status": "pending"}


# --- GET /api/reports ------------------------------------------------------------


def test_reports_rejects_unknown_evaluation():
    response = client.get("/api/reports/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_reports_rejects_when_not_yet_complete():
    evaluation_id = _create_evaluation_with_submission()
    response = client.get(f"/api/reports/{evaluation_id}")
    assert response.status_code == 409
    assert response.json()["error"] == "conflict"
    assert "pending" in response.json()["detail"].lower()


# --- PATCH /api/reports/{id}/results/{requirement_id} (officer review) --------


def _complete_evaluation(monkeypatch) -> str:
    evaluation_id = _create_evaluation_with_submission()
    monkeypatch.setattr(routes_evaluate, "process_document", lambda path: [])
    monkeypatch.setattr(routes_evaluate, "evaluate_requirements", lambda reqs, docs, d: [])
    monkeypatch.setattr(routes_evaluate, "build_report", lambda eid, results: _fake_report(eid))
    client.post("/api/evaluate", json={"evaluation_id": evaluation_id})
    return evaluation_id


def test_review_result_records_officer_override(monkeypatch):
    evaluation_id = _complete_evaluation(monkeypatch)

    response = client.patch(
        f"/api/reports/{evaluation_id}/results/req-1",
        json={"status": "Non-Compliant", "note": "Certificate address does not match site location."},
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["officer_review"]["status"] == "Non-Compliant"
    assert result["officer_review"]["note"] == "Certificate address does not match site location."
    # The system's own finding is untouched by the officer's review.
    assert result["status"] == "Compliant"


def test_review_result_persists_and_can_be_overwritten(monkeypatch):
    evaluation_id = _complete_evaluation(monkeypatch)

    client.patch(f"/api/reports/{evaluation_id}/results/req-1", json={"status": "Compliant"})
    second = client.patch(
        f"/api/reports/{evaluation_id}/results/req-1", json={"status": "Needs Review", "note": "changed my mind"}
    )
    assert second.status_code == 200
    result = second.json()["results"][0]
    assert result["officer_review"]["status"] == "Needs Review"
    assert result["officer_review"]["note"] == "changed my mind"

    fetched = client.get(f"/api/reports/{evaluation_id}").json()
    assert fetched["results"][0]["officer_review"]["status"] == "Needs Review"


def test_review_result_rejects_unknown_evaluation():
    response = client.patch("/api/reports/does-not-exist/results/req-1", json={"status": "Compliant"})
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_review_result_rejects_unknown_requirement(monkeypatch):
    evaluation_id = _complete_evaluation(monkeypatch)

    response = client.patch(f"/api/reports/{evaluation_id}/results/does-not-exist", json={"status": "Compliant"})
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_review_result_rejects_when_not_yet_complete():
    evaluation_id = _create_evaluation_with_submission()

    response = client.patch(f"/api/reports/{evaluation_id}/results/req-1", json={"status": "Compliant"})
    assert response.status_code == 409
    assert response.json()["error"] == "conflict"
