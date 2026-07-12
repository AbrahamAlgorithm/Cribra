"""POST /api/requirements — default / upload / manual checklist creation.

Endpoints implemented in Milestone 1 (default, manual) and Milestone 7 (upload).
"""

from fastapi import APIRouter

router = APIRouter(tags=["requirements"])
