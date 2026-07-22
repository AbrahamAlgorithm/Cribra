"""In-memory / file-backed store for evaluations, submissions, and job status.

Implemented in Milestone 1.
"""

from __future__ import annotations

import threading

from app.models.domain import Evaluation, Submission


class NotFoundError(KeyError):
    """Raised when a lookup by id finds nothing."""


class JobStore:
    """Process-local in-memory store. Not persisted across restarts.

    The tech stack (SPEC.md Section 2) does not specify a database, so an
    in-memory store is sufficient for the single-process MVP. Swap for a real
    persistence layer in Phase 8 if the deployment target needs
    multi-instance or restart-safe state.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._evaluations: dict[str, Evaluation] = {}
        self._submissions: dict[str, Submission] = {}

    def save_evaluation(self, evaluation: Evaluation) -> Evaluation:
        with self._lock:
            self._evaluations[evaluation.id] = evaluation
        return evaluation

    def get_evaluation(self, evaluation_id: str) -> Evaluation:
        with self._lock:
            evaluation = self._evaluations.get(evaluation_id)
        if evaluation is None:
            raise NotFoundError(evaluation_id)
        return evaluation

    def save_submission(self, submission: Submission) -> Submission:
        with self._lock:
            self._submissions[submission.id] = submission
        return submission

    def get_submission(self, submission_id: str) -> Submission:
        with self._lock:
            submission = self._submissions.get(submission_id)
        if submission is None:
            raise NotFoundError(submission_id)
        return submission


_store = JobStore()


def get_job_store() -> JobStore:
    return _store
