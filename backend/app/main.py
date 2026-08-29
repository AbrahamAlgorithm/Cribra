"""Cribra backend — FastAPI application entry point."""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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

# Local frontend dev server (Vite) + the deployed Cloud Run frontend. Cribra
# has no browser-based auth/session state yet, so an open-but-explicit
# allowlist is sufficient here.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://cribra-frontend-taqq76r7ua-uc.a.run.app",
        "https://cribra-frontend-179103012566.us-central1.run.app",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
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
    FastAPI's default behaviour would nest that under a "detail" key.
    """
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": str(exc.detail), "detail": str(exc.detail)},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Milestone 5: bad request bodies (missing/invalid fields) get the same
    error shape as everything else, instead of FastAPI's default
    `{"detail": [...]}` pydantic error list.
    """
    return JSONResponse(
        status_code=400,
        content={"error": "bad_request", "detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Milestone 5: never leak a stack trace to the client (SPEC.md Section 7).

    The real exception is logged server-side (evaluation IDs/status only
    ground rule applies to *deliberate* logging elsewhere — this is a
    last-resort safety net for genuinely unexpected errors, so the full
    exception is logged for debugging, never returned in the response body).
    """
    logging.getLogger(__name__).exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
