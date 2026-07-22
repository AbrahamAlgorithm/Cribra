"""PATCH /api/evaluations/{evaluation_id} — edit evaluation_date pre-run.

Endpoint added in Milestone 1 (extension) per SPEC.md Section 4.3: evaluation_date
defaults to the checklist's creation date and may be corrected any time before the
evaluation actually runs. Once status leaves "pending" the date is immutable — the
run has (or is about to have) used it, and editing it after the fact would make the
certificate-expiry check (Milestone 4A) retroactively inconsistent with its own report.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.domain import Evaluation
from app.storage.job_store import NotFoundError, get_job_store

router = APIRouter(tags=["evaluations"])


class EvaluationDatePatch(BaseModel):
    evaluation_date: date


@router.patch("/evaluations/{evaluation_id}", response_model=Evaluation)
def patch_evaluation_date(evaluation_id: str, payload: EvaluationDatePatch) -> Evaluation:
    store = get_job_store()
    try:
        evaluation = store.get_evaluation(evaluation_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "detail": f"Evaluation '{evaluation_id}' does not exist.",
            },
        ) from exc

    if evaluation.status != "pending":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "detail": "evaluation_date can only be edited while status is "
                f"'pending' (current status: '{evaluation.status}').",
            },
        )

    evaluation.evaluation_date = payload.evaluation_date
    store.save_evaluation(evaluation)
    return evaluation
