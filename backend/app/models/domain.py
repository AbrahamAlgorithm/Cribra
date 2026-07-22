"""Domain model: Evaluation, Requirement, RequirementSource, Submission.

Implemented in Milestone 1 per SPEC.md, Section 5.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.reasoning.schema import ComplianceReport


class RequirementSource(BaseModel):
    type: Literal["default", "uploaded", "manual"]
    document_name: str | None = None
    section_reference: str | None = None


class Requirement(BaseModel):
    id: str
    name: str
    description: str
    is_mandatory: bool
    source: RequirementSource


class Evaluation(BaseModel):
    """Owns a single evaluation session — replaces the earlier 'Tender' concept.

    Cribra models an evaluation session, not the procurement process itself.
    """

    id: str
    requirement_source_type: Literal["default", "uploaded", "manual"]
    requirements: list[Requirement]
    submission_id: str | None = None
    evaluation_date: date
    status: Literal[
        "pending", "ingesting", "retrieving", "evaluating", "generating_report", "complete", "failed"
    ] = "pending"
    report: "ComplianceReport | None" = None


class Submission(BaseModel):
    id: str
    evaluation_id: str
    documents: list[str]
