"""Global exception handlers for FastAPI.

Provides centralized error handling with uniform response format.
Internal errors are logged with full traceback but never exposed to clients.
"""

import logging
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Uniform error response model for all API errors."""

    detail: str
    field: Optional[str] = None


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors (422)."""
        errors = exc.errors()
        first_error = errors[0] if errors else {}
        field = (
            " -> ".join(str(loc) for loc in first_error.get("loc", []))
            if first_error
            else None
        )
        detail = (
            first_error.get("msg", "Validation error")
            if first_error
            else "Validation error"
        )

        return JSONResponse(
            status_code=422,
            content={"detail": detail, "field": field},
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """Handle HTTP exceptions (4xx, 5xx)."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unhandled exceptions (500).

        Logs the full traceback but returns a generic message to the client.
        """
        logger.error(
            "Unhandled exception: %s",
            str(exc),
            exc_info=True,
            extra={"traceback": traceback.format_exc()},
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
