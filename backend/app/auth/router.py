"""Authentication router with register and login endpoints."""

import uuid

from fastapi import APIRouter, HTTPException, status

from backend.app.auth.schemas import LoginRequest, RegisterRequest, TokenResponse
from backend.app.auth.service import create_access_token, hash_password, verify_password
from backend.app.db.user_repository import create_user, get_user_by_username

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest) -> dict:
    """Register a new user."""
    existing = get_user_by_username(request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user_id = str(uuid.uuid4())
    password_hash = hash_password(request.password)
    create_user(user_id, request.username, password_hash)

    return {"message": "User created successfully", "user_id": user_id}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT token."""
    user = get_user_by_username(request.username)
    if not user or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(user["user_id"], user["username"])
    return TokenResponse(access_token=token)
