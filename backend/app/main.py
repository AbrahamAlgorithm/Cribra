"""Cribra backend — FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.api.routes_evaluate import router as evaluate_router
from app.api.routes_requirements import router as requirements_router
from app.api.routes_status import router as status_router
from app.api.routes_submissions import router as submissions_router
from app.config import get_settings

settings = get_settings()

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="Cribra Backend",
    description="Technical Compliance Evaluation for procurement submissions.",
    version="0.1.0",
)

app.include_router(requirements_router, prefix="/api")
app.include_router(submissions_router, prefix="/api")
app.include_router(evaluate_router, prefix="/api")
app.include_router(status_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
