"""Tests for POST /api/submissions (Milestone 1)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_evaluation() -> str:
    response = client.post("/api/requirements", json={"mode": "default"})
    return response.json()["id"]


def test_submission_attaches_to_existing_evaluation():
    evaluation_id = _create_evaluation()

    response = client.post(
        "/api/submissions",
        data={"evaluation_id": evaluation_id},
        files=[("files", ("cac.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    assert response.status_code == 201

    body = response.json()
    assert body["evaluation_id"] == evaluation_id
    assert len(body["documents"]) == 1


def test_submission_accepts_multiple_documents():
    evaluation_id = _create_evaluation()

    response = client.post(
        "/api/submissions",
        data={"evaluation_id": evaluation_id},
        files=[
            ("files", ("cac.pdf", b"%PDF-1.4 fake", "application/pdf")),
            ("files", ("tax_clearance.docx", b"fake docx bytes", "application/vnd.openxmlformats")),
        ],
    )
    assert response.status_code == 201
    assert len(response.json()["documents"]) == 2


def test_submission_rejects_unknown_evaluation():
    response = client.post(
        "/api/submissions",
        data={"evaluation_id": "does-not-exist"},
        files=[("files", ("cac.pdf", b"%PDF-1.4 fake", "application/pdf"))],
    )
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_submission_rejects_unsupported_file_type():
    evaluation_id = _create_evaluation()

    response = client.post(
        "/api/submissions",
        data={"evaluation_id": evaluation_id},
        files=[("files", ("virus.exe", b"MZ", "application/octet-stream"))],
    )
    assert response.status_code == 400
    assert response.json()["error"] == "unsupported_file_type"
