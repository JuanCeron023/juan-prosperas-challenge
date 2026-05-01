"""Unit tests for the authentication service."""

import time
from unittest.mock import patch

import jwt
import pytest

from backend.app.auth.service import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestHashPassword:
    """Tests for hash_password function."""

    def test_hash_password_returns_bcrypt_hash(self):
        """hash_password returns a string that starts with the bcrypt prefix."""
        result = hash_password("mysecretpassword")
        assert isinstance(result, str)
        assert result.startswith("$2b$")

    def test_hash_password_different_for_same_input(self):
        """Each call produces a different hash due to random salt."""
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2


class TestVerifyPassword:
    """Tests for verify_password function."""

    def test_verify_password_correct(self):
        """verify_password returns True for matching password and hash."""
        password = "correctpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password returns False for non-matching password."""
        hashed = hash_password("original")
        assert verify_password("wrong", hashed) is False


class TestCreateAccessToken:
    """Tests for create_access_token function."""

    @patch("backend.app.auth.service.settings")
    def test_create_access_token_returns_valid_jwt(self, mock_settings):
        """create_access_token returns a decodable JWT with correct claims."""
        mock_settings.jwt_secret = "test-secret"
        mock_settings.jwt_expiration_minutes = 60

        token = create_access_token("user-123", "testuser")

        payload = jwt.decode(token, "test-secret", algorithms=["HS256"])
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert "exp" in payload
        assert "iat" in payload


class TestDecodeToken:
    """Tests for decode_token function."""

    @patch("backend.app.auth.service.settings")
    def test_decode_token_returns_payload(self, mock_settings):
        """decode_token returns the token payload for a valid token."""
        mock_settings.jwt_secret = "test-secret"
        mock_settings.jwt_expiration_minutes = 60

        token = create_access_token("user-456", "anotheruser")
        payload = decode_token(token)

        assert payload["sub"] == "user-456"
        assert payload["username"] == "anotheruser"

    @patch("backend.app.auth.service.settings")
    def test_decode_token_expired_raises(self, mock_settings):
        """decode_token raises InvalidTokenError for an expired token."""
        mock_settings.jwt_secret = "test-secret"
        mock_settings.jwt_expiration_minutes = 0  # Immediate expiration

        token = create_access_token("user-789", "expireduser")
        # Token is already expired since expiration is 0 minutes
        time.sleep(0.1)

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(token)

    @patch("backend.app.auth.service.settings")
    def test_decode_token_invalid_raises(self, mock_settings):
        """decode_token raises InvalidTokenError for a tampered token."""
        mock_settings.jwt_secret = "test-secret"
        mock_settings.jwt_expiration_minutes = 60

        # Create a token with a different secret
        bad_token = jwt.encode(
            {"sub": "user-000", "username": "hacker"},
            "wrong-secret",
            algorithm="HS256",
        )

        with pytest.raises(jwt.InvalidTokenError):
            decode_token(bad_token)
