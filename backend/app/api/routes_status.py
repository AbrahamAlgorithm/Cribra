"""GET /api/status/{evaluation_id} and GET /api/reports/{evaluation_id}.

Endpoints implemented in Milestone 5.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.domain import EvaluationStatus
from app.reasoning.schema import ComplianceReport, OfficerReview
from app.storage.job_store import NotFoundError, get_job_store

router = APIRouter(tags=["status"])


class StatusResponse(BaseModel):
    evaluation_id: str
    status: EvaluationStatus


def _get_evaluation_or_404(evaluation_id: str):
    store = get_job_store()
    try:
        return store.get_evaluation(evaluation_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "detail": f"Evaluation '{evaluation_id}' does not exist."},
        ) from exc


@router.get("/status/{evaluation_id}", response_model=StatusResponse)
def get_status(evaluation_id: str) -> StatusResponse:
    evaluation = _get_evaluation_or_404(evaluation_id)
    return StatusResponse(evaluation_id=evaluation.id, status=evaluation.status)


@router.get("/reports/{evaluation_id}", response_model=ComplianceReport)
def get_report(evaluation_id: str) -> ComplianceReport:
    evaluation = _get_evaluation_or_404(evaluation_id)

    if evaluation.status == "failed":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "detail": "This evaluation failed during processing and has no report. Check server logs.",
            },
        )

    if evaluation.report is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "detail": f"Evaluation is not yet complete (status: '{evaluation.status}').",
            },
        )

    return evaluation.report


class OfficerReviewIn(BaseModel):
    status: Literal["Compliant", "Non-Compliant", "Needs Review"]
    note: str | None = None


@router.patch("/reports/{evaluation_id}/results/{requirement_id}", response_model=ComplianceReport)
def review_result(evaluation_id: str, requirement_id: str, payload: OfficerReviewIn) -> ComplianceReport:
    """Record (or update) the procurement officer's own judgement on one result.

    Overwrites any prior review on this requirement — an officer changing
    their mind is expected, not an error. Does not touch `status`, the
    system's own finding; the review is stored alongside it.
    """
    evaluation = _get_evaluation_or_404(evaluation_id)

    if evaluation.report is None:
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "detail": f"Evaluation is not yet complete (status: '{evaluation.status}').",
            },
        )

    for result in evaluation.report.results:
        if result.requirement_id == requirement_id:
            result.officer_review = OfficerReview(status=payload.status, note=payload.note, reviewed_at=datetime.now())
            get_job_store().save_evaluation(evaluation)
            return evaluation.report

    raise HTTPException(
        status_code=404,
        detail={
            "error": "not_found",
            "detail": f"Requirement '{requirement_id}' is not part of this report.",
        },
    )
