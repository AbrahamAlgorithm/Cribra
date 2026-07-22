"""Cribra backend — FastAPI application entry point."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.routes_evaluate import router as evaluate_router
from app.api.routes_evaluations import router as evaluations_router
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
app.include_router(evaluations_router, prefix="/api")
app.include_router(status_router, prefix="/api")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Flatten HTTPException responses to SPEC.md Section 7's error shape.

    Route handlers raise HTTPException(detail={"error": ..., "detail": ...});
    FastAPI's default behaviour would nest that under a "detail" key. Full
    coverage (422 validation errors, masked 500s) is Milestone 5's scope —
    this covers the shape for the endpoints built so far.
    """
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "detail": str(exc.detail)},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
