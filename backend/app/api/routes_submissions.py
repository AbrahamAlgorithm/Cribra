"""POST /api/submissions — upload contractor submission documents.

Endpoints implemented in Milestone 1.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import get_settings
from app.models.domain import Submission
from app.storage.job_store import NotFoundError, get_job_store

router = APIRouter(tags=["submissions"])

# Extraction (Milestone 2) is scoped to PDF/DOCX + image vision-fallback
# (SPEC.md Section 2, Phase 2 logic) — reject anything else at the door.
ALLOWED_SUFFIXES = {".pdf", ".docx", ".jpg", ".jpeg", ".png"}


@router.post("/submissions", response_model=Submission, status_code=201)
def create_submission(
    evaluation_id: str = Form(...),
    files: list[UploadFile] = File(...),
) -> Submission:
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

    if not files:
        raise HTTPException(
            status_code=400,
            detail={"error": "bad_request", "detail": "At least one document must be uploaded."},
        )

    settings = get_settings()
    upload_dir = Path(settings.upload_dir) / evaluation_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    document_paths: list[str] = []
    for upload in files:
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_file_type",
                    "detail": f"'{upload.filename}' has unsupported type "
                    f"'{suffix or 'unknown'}'. Allowed: {sorted(ALLOWED_SUFFIXES)}.",
                },
            )
        dest = upload_dir / f"{uuid4()}_{upload.filename}"
        dest.write_bytes(upload.file.read())
        document_paths.append(str(dest))

    submission = Submission(id=str(uuid4()), evaluation_id=evaluation_id, documents=document_paths)
    store.save_submission(submission)

    evaluation.submission_id = submission.id
    store.save_evaluation(evaluation)

    return submission
