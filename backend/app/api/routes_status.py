"""GET /api/status/{evaluation_id} and GET /api/reports/{evaluation_id}.

Endpoints implemented in Milestone 5.
"""

from fastapi import APIRouter

router = APIRouter(tags=["status"])
