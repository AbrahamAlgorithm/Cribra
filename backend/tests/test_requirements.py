"""Tests for POST /api/requirements (Milestone 1 — default & manual modes)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_default_mode_returns_ten_item_checklist():
    response = client.post("/api/requirements", json={"mode": "default"})
    assert response.status_code == 201

    body = response.json()
    assert len(body["requirements"]) == 10
    assert all(r["source"]["type"] == "default" for r in body["requirements"])
    assert body["requirement_source_type"] == "default"
    assert body["status"] == "pending"
    assert body["submission_id"] is None
    assert body["report"] is None


def test_get_default_requirements_returns_the_default_checklist():
    response = client.get("/api/requirements/default")
    assert response.status_code == 200

    body = response.json()
    assert len(body) == 10
    assert all(r["source"]["type"] == "default" for r in body)
    assert body[0]["name"] == "CAC Certificate"


def test_manual_mode_stores_officer_defined_requirements():
    payload = {
        "mode": "manual",
        "requirements": [
            {
                "name": "Site Visit Report",
                "description": "Signed site visit acknowledgement.",
                "is_mandatory": True,
            }
        ],
    }
    response = client.post("/api/requirements", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert len(body["requirements"]) == 1
    assert body["requirements"][0]["name"] == "Site Visit Report"
    assert body["requirements"][0]["source"]["type"] == "manual"


def test_manual_mode_without_requirements_is_rejected():
    response = client.post("/api/requirements", json={"mode": "manual"})
    assert response.status_code == 400
    assert response.json()["error"] == "bad_request"


def test_upload_mode_not_yet_implemented():
    response = client.post("/api/requirements", json={"mode": "upload"})
    assert response.status_code == 400
    assert response.json()["error"] == "not_implemented"
