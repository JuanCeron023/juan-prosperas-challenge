"""Unit tests for the user repository module."""

import uuid
from unittest.mock import patch

import pytest

from backend.app.db import user_repository


class TestCreateUser:
    """Tests for the create_user function."""

    def test_create_user_stores_all_fields(self, dynamodb_users_table):
        """create_user should store user_id, username, password_hash, and created_at."""
        user_id = str(uuid.uuid4())
        username = "testuser"
        password_hash = "$2b$12$somehashvalue"

        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            result = user_repository.create_user(user_id, username, password_hash)

        assert result["user_id"] == user_id
        assert result["username"] == username
        assert result["password_hash"] == password_hash
        assert "created_at" in result

    def test_create_user_sets_created_at_automatically(self, dynamodb_users_table):
        """create_user should automatically set created_at to an ISO 8601 timestamp."""
        user_id = str(uuid.uuid4())

        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            result = user_repository.create_user(user_id, "alice", "hash123")

        # Verify created_at is a valid ISO 8601 string
        from datetime import datetime

        created_at = datetime.fromisoformat(result["created_at"])
        assert created_at is not None

    def test_create_user_persists_to_dynamodb(self, dynamodb_users_table):
        """create_user should persist the user item in DynamoDB."""
        user_id = str(uuid.uuid4())
        username = "bob"
        password_hash = "$2b$12$anotherhash"

        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            user_repository.create_user(user_id, username, password_hash)

            # Verify item exists in table
            response = table.get_item(Key={"user_id": user_id})
            item = response["Item"]

        assert item["user_id"] == user_id
        assert item["username"] == username
        assert item["password_hash"] == password_hash


class TestGetUserByUsername:
    """Tests for the get_user_by_username function."""

    def test_get_user_by_username_returns_user(self, dynamodb_users_table):
        """get_user_by_username should return the user when found."""
        user_id = str(uuid.uuid4())
        username = "charlie"
        password_hash = "$2b$12$charlieHash"

        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            # Create user first
            user_repository.create_user(user_id, username, password_hash)

            # Query by username
            result = user_repository.get_user_by_username(username)

        assert result is not None
        assert result["user_id"] == user_id
        assert result["username"] == username
        assert result["password_hash"] == password_hash

    def test_get_user_by_username_returns_none_when_not_found(self, dynamodb_users_table):
        """get_user_by_username should return None when no user matches."""
        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            result = user_repository.get_user_by_username("nonexistent")

        assert result is None

    def test_get_user_by_username_returns_correct_user_among_multiple(self, dynamodb_users_table):
        """get_user_by_username should return the correct user when multiple exist."""
        with patch.object(user_repository, "_get_users_table") as mock_table:
            table = dynamodb_users_table.Table("users")
            mock_table.return_value = table

            # Create multiple users
            user1_id = str(uuid.uuid4())
            user2_id = str(uuid.uuid4())
            user_repository.create_user(user1_id, "alice", "hash1")
            user_repository.create_user(user2_id, "bob", "hash2")

            # Query for specific user
            result = user_repository.get_user_by_username("bob")

        assert result is not None
        assert result["user_id"] == user2_id
        assert result["username"] == "bob"
