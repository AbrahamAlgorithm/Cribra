"""Requirements endpoints for default / upload / manual checklist flows.

Endpoints implemented in Milestone 1 (default, manual) and Milestone 7 (upload).
"""

from __future__ import annotations

from datetime import date
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.domain import Evaluation, Requirement, RequirementSource
from app.storage.job_store import get_job_store

router = APIRouter(tags=["requirements"])

# The 10-item default BPP technical-compliance checklist (SPEC.md Section 4.1).
DEFAULT_CHECKLIST: list[tuple[str, str, bool]] = [
    (
        "CAC Certificate",
        "Certificate of Incorporation / business registration issued by the "
        "Corporate Affairs Commission.",
        True,
    ),
    (
        "Tax Clearance Certificate",
        "Valid tax clearance certificate covering the last 3 years.",
        True,
    ),
    (
        "PENCOM Compliance Certificate",
        "Certificate of compliance with the Pension Reform Act, issued by PenCom.",
        True,
    ),
    (
        "ITF Compliance Certificate",
        "Compliance certificate issued by the Industrial Training Fund.",
        True,
    ),
    (
        "NSITF Compliance Certificate",
        "Compliance certificate issued by the Nigeria Social Insurance Trust Fund.",
        True,
    ),
    (
        "Audited Accounts",
        "Audited financial statements for the last 3 years.",
        True,
    ),
    (
        "Professional Registration",
        "Evidence of professional body registration (COREN, CORBON, etc.) "
        "relevant to the scope of work.",
        True,
    ),
    (
        "Key Personnel CVs",
        "Curriculum vitae for proposed key personnel, showing relevant "
        "qualifications and experience.",
        True,
    ),
    (
        "Similar Project Experience",
        "Evidence of 3-5 completed jobs of similar scope in the last 5 years, "
        "each with an award letter and a completion certificate.",
        True,
    ),
    (
        "Equipment Schedule",
        "Schedule of equipment (owned or leased) relevant to executing the contract.",
        True,
    ),
]

_MANUAL_SOURCE_FALLBACK = RequirementSource(
    type="manual",
    document_name="As specified in evaluation checklist",
    section_reference=None,
)


class ManualRequirementIn(BaseModel):
    name: str
    description: str
    is_mandatory: bool = True
    source: RequirementSource | None = None


class RequirementsCreateRequest(BaseModel):
    mode: Literal["default", "manual", "upload"]
    requirements: list[ManualRequirementIn] | None = None


def _build_default_requirements() -> list[Requirement]:
    return [
        Requirement(
            id=str(uuid4()),
            name=name,
            description=description,
            is_mandatory=is_mandatory,
            source=RequirementSource(
                type="default",
                document_name="BPP Default Technical Compliance Checklist",
                section_reference=None,
            ),
        )
        for name, description, is_mandatory in DEFAULT_CHECKLIST
    ]


@router.get("/requirements/default", response_model=list[Requirement])
def get_default_requirements() -> list[Requirement]:
    return _build_default_requirements()


def _build_manual_requirements(items: list[ManualRequirementIn]) -> list[Requirement]:
    return [
        Requirement(
            id=str(uuid4()),
            name=item.name,
            description=item.description,
            is_mandatory=item.is_mandatory,
            source=item.source or _MANUAL_SOURCE_FALLBACK,
        )
        for item in items
    ]


@router.post("/requirements", response_model=Evaluation, status_code=201)
def create_requirements(payload: RequirementsCreateRequest) -> Evaluation:
    if payload.mode == "default":
        requirements = _build_default_requirements()
    elif payload.mode == "manual":
        if not payload.requirements:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "bad_request",
                    "detail": "mode 'manual' requires a non-empty 'requirements' list.",
                },
            )
        requirements = _build_manual_requirements(payload.requirements)
    else:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "not_implemented",
                "detail": "mode 'upload' is not yet implemented — deferred to "
                "Phase 7 / SPEC.md Section 8, Milestone 7.",
            },
        )

    evaluation = Evaluation(
        id=str(uuid4()),
        requirement_source_type=payload.mode,
        requirements=requirements,
        submission_id=None,
        # Placeholder: set to the checklist's creation date for now. SPEC.md
        # Section 4.3 defines this as "the date Cribra runs the check" —
        # Milestone 5's POST /api/evaluate will overwrite it with the actual
        # evaluation-run date before certificate expiry checks (Milestone 4A) use it.
        evaluation_date=date.today(),
        status="pending",
        report=None,
    )
    get_job_store().save_evaluation(evaluation)
    return evaluation
