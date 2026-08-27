"""POST /api/evaluate — start an evaluation run.

Endpoint implemented in Milestone 5. Runs in a background task rather than
blocking the request — a real run against the 158-page field-collected
submission took 40-70+ seconds end to end (Milestone 4's real-data
validation), far past what's reasonable for a synchronous HTTP response.
The client polls `GET /api/status/{evaluation_id}` (routes_status.py) until
`"complete"`, then fetches `GET /api/reports/{evaluation_id}`.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.ingestion.pipeline import process_document
from app.models.domain import Evaluation
from app.reasoning.evaluator import build_report, evaluate_requirements
from app.storage.job_store import NotFoundError, get_job_store

logger = logging.getLogger(__name__)

router = APIRouter(tags=["evaluate"])


class EvaluateRequest(BaseModel):
    evaluation_id: str


def _run_evaluation(evaluation_id: str) -> None:
    """The actual pipeline: Milestone 2 extraction -> Milestone 4 4A/4B -> report.

    Status transitions logged and persisted at each real phase boundary.
    "retrieving" (a status value the domain model supports) is deliberately
    not surfaced as its own transition here — Milestone 3's retrieval runs
    per-requirement *inside* each 4B call, not as one separate global step,
    so there's no real, distinct moment to report it at without faking a
    transition that doesn't correspond to actual work.
    """
    store = get_job_store()
    evaluation = store.get_evaluation(evaluation_id)
    try:
        submission = store.get_submission(evaluation.submission_id)

        extracted_documents = []
        for document_path in submission.documents:
            extracted_documents.extend(process_document(document_path))

        evaluation.status = "evaluating"
        store.save_evaluation(evaluation)
        results = evaluate_requirements(evaluation.requirements, extracted_documents, evaluation.evaluation_date)

        evaluation.status = "generating_report"
        store.save_evaluation(evaluation)
        report = build_report(evaluation.id, results)

        evaluation.report = report
        evaluation.status = "complete"
        store.save_evaluation(evaluation)
    except Exception:
        # Logging.md ground rule (SPEC.md Section 8, Milestone 8): evaluation
        # IDs and statuses only, no PII/document contents — logger.exception
        # here logs the exception type/message/traceback, never document text.
        logger.exception("Evaluation %s failed", evaluation_id)
        evaluation.status = "failed"
        store.save_evaluation(evaluation)


@router.post("/evaluate", response_model=Evaluation, status_code=202)
def start_evaluation(payload: EvaluateRequest, background_tasks: BackgroundTasks) -> Evaluation:
    store = get_job_store()
    try:
        evaluation = store.get_evaluation(payload.evaluation_id)
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "detail": f"Evaluation '{payload.evaluation_id}' does not exist.",
            },
        ) from exc

    if evaluation.status != "pending":
        raise HTTPException(
            status_code=409,
            detail={
                "error": "conflict",
                "detail": f"Evaluation is already '{evaluation.status}' — cannot start again.",
            },
        )

    if evaluation.submission_id is None:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "bad_request",
                "detail": "No submission has been attached to this evaluation yet.",
            },
        )

    evaluation.status = "ingesting"
    store.save_evaluation(evaluation)

    background_tasks.add_task(_run_evaluation, evaluation.id)
    return evaluation
