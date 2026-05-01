"""Pydantic schemas for authentication endpoints."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    """Response body for POST /auth/login."""
    access_token: str
    token_type: str = "bearer"
