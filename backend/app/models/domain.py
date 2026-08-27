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


# Named alias (Milestone 5) so routes_status.py's StatusResponse can share
# this exact set of values with Evaluation.status rather than repeating the
# literal list in a second place that could drift out of sync.
EvaluationStatus = Literal["pending", "ingesting", "retrieving", "evaluating", "generating_report", "complete", "failed"]


class Evaluation(BaseModel):
    """Owns a single evaluation session — replaces the earlier 'Tender' concept.

    Cribra models an evaluation session, not the procurement process itself.
    """

    id: str
    requirement_source_type: Literal["default", "uploaded", "manual"]
    requirements: list[Requirement]
    submission_id: str | None = None
    evaluation_date: date
    status: EvaluationStatus = "pending"
    report: "ComplianceReport | None" = None


class Submission(BaseModel):
    id: str
    evaluation_id: str
    documents: list[str]
