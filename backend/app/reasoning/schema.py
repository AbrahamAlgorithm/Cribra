"""Structured output contract: RequirementResult, ComplianceSummary, ComplianceReport.

Type definitions implemented in Milestone 1, ahead of the schedule implied by
SPEC.md Section 8 (Milestone 4), because `Evaluation.report` (Section 5) needs
the `ComplianceReport` type to exist. The evaluator logic that actually
*produces* these objects (deterministic + RAG reasoning) remains Milestone 4A/4B.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.models.domain import Evaluation, RequirementSource


class RequirementResult(BaseModel):
    requirement_id: str
    requirement_name: str
    status: Literal["Compliant", "Non-Compliant", "Needs Review"]
    evidence_found: str | None
    requirement_source: RequirementSource
    justification: str
    confidence_note: str | None = None


class ComplianceSummary(BaseModel):
    requirements_evaluated: int
    compliant: int
    non_compliant: int
    needs_review: int
    compliance_score: float


class ComplianceReport(BaseModel):
    evaluation_id: str
    generated_at: datetime
    results: list[RequirementResult]
    summary: ComplianceSummary
    observations: list[str]
    overall_assessment: str


# `Evaluation.report` references `ComplianceReport` as a forward reference
# (see app/models/domain.py) to avoid a circular import at module load time.
Evaluation.model_rebuild()
