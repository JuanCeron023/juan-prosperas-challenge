"""Unit tests for global exception handlers."""

import logging

import pytest
import pytest_asyncio
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, Field

from app.errors.handlers import ErrorResponse, register_exception_handlers


@pytest.fixture
def app():
    """Create a FastAPI app with exception handlers registered."""
    test_app = FastAPI(debug=False)
    register_exception_handlers(test_app)

    class StrictBody(BaseModel):
        name: str = Field(min_length=3)
        age: int

    @test_app.post("/validate")
    async def validate_endpoint(body: StrictBody):
        return {"ok": True}

    @test_app.get("/not-found")
    async def not_found_endpoint():
        raise HTTPException(status_code=404, detail="Resource not found")

    @test_app.get("/forbidden")
    async def forbidden_endpoint():
        raise HTTPException(status_code=403, detail="Forbidden")

    @test_app.get("/crash")
    async def crash_endpoint():
        raise RuntimeError("Something went terribly wrong")

    return test_app


@pytest_asyncio.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_validation_error_returns_422_with_field(client):
    """RequestValidationError returns 422 with field and detail."""
    response = await client.post("/validate", json={"name": "ab"})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "field" in body
    assert body["field"] is not None


@pytest.mark.asyncio
async def test_validation_error_missing_field(client):
    """Missing required field returns 422 with field info."""
    response = await client.post("/validate", json={"name": "valid"})
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
    assert "field" in body


@pytest.mark.asyncio
async def test_http_exception_404(client):
    """HTTPException 404 returns proper error response."""
    response = await client.get("/not-found")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Resource not found"


@pytest.mark.asyncio
async def test_http_exception_403(client):
    """HTTPException 403 returns proper error response."""
    response = await client.get("/forbidden")
    assert response.status_code == 403
    body = response.json()
    assert body["detail"] == "Forbidden"


@pytest.mark.asyncio
async def test_generic_exception_returns_500_without_details(client):
    """Unhandled exceptions return 500 with generic message, no internal details."""
    response = await client.get("/crash")
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Internal server error"
    # Must NOT expose internal error details
    assert "terribly wrong" not in body["detail"]


@pytest.mark.asyncio
async def test_generic_exception_logs_error(client, caplog):
    """Unhandled exceptions are logged with ERROR level and traceback."""
    with caplog.at_level(logging.ERROR, logger="app.errors.handlers"):
        response = await client.get("/crash")
    assert response.status_code == 500
    assert "Unhandled exception" in caplog.text
    assert "Something went terribly wrong" in caplog.text


def test_error_response_model():
    """ErrorResponse model has correct fields."""
    err = ErrorResponse(detail="Something failed", field="username")
    assert err.detail == "Something failed"
    assert err.field == "username"

    err_no_field = ErrorResponse(detail="Generic error")
    assert err_no_field.field is None
