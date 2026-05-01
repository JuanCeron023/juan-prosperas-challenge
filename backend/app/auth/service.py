"""Authentication service: password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(user_id: str, username: str) -> str:
    """Create a JWT access token.

    The token contains:
        - sub: user_id
        - username: the user's username
        - iat: issued at timestamp
        - exp: expiration timestamp
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expiration_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token.

    Raises:
        jwt.InvalidTokenError: If the token is expired, has an invalid
            signature, or is otherwise malformed.
    """
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
