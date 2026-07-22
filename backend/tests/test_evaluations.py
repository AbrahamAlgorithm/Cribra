"""Tests for PATCH /api/evaluations/{evaluation_id} (Milestone 1 extension).

evaluation_date defaults to date.today() at checklist creation and is editable
only while the evaluation is still "pending" — see SPEC.md Section 4.3.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.storage.job_store import get_job_store

client = TestClient(app)


def _create_evaluation() -> str:
    response = client.post("/api/requirements", json={"mode": "default"})
    return response.json()["id"]


def test_patch_updates_evaluation_date_while_pending():
    evaluation_id = _create_evaluation()

    response = client.patch(
        f"/api/evaluations/{evaluation_id}",
        json={"evaluation_date": "2026-08-01"},
    )
    assert response.status_code == 200
    assert response.json()["evaluation_date"] == "2026-08-01"
    assert response.json()["status"] == "pending"


def test_patch_rejects_unknown_evaluation():
    response = client.patch(
        "/api/evaluations/does-not-exist",
        json={"evaluation_date": "2026-08-01"},
    )
    assert response.status_code == 404
    assert response.json()["error"] == "not_found"


def test_patch_rejects_once_status_leaves_pending():
    evaluation_id = _create_evaluation()

    store = get_job_store()
    evaluation = store.get_evaluation(evaluation_id)
    evaluation.status = "evaluating"
    store.save_evaluation(evaluation)

    response = client.patch(
        f"/api/evaluations/{evaluation_id}",
        json={"evaluation_date": "2026-08-01"},
    )
    assert response.status_code == 409
    assert response.json()["error"] == "conflict"
