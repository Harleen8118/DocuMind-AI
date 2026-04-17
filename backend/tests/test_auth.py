"""Tests for authentication endpoints."""

import pytest
import pytest_asyncio


@pytest.mark.asyncio
class TestAuthRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["username"] == "newuser"
        assert "id" in data["user"]

    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "different_user",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with existing username fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": "testuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 409
        assert "already taken" in response.json()["detail"]

    async def test_register_invalid_email(self, client):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": "validuser",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client):
        """Test registration with too-short password fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "validuser",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_register_short_username(self, client):
        """Test registration with too-short username fails."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "username": "ab",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestAuthLogin:
    """Tests for POST /api/v1/auth/login."""

    async def test_login_success(self, client, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    async def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_login_nonexistent_email(self, client):
        """Test login with non-existent email fails."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword123",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
class TestAuthMe:
    """Tests for GET /api/v1/auth/me."""

    async def test_get_me_authenticated(self, client, auth_headers):
        """Test getting current user info with valid token."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    async def test_get_me_unauthenticated(self, client):
        """Test getting current user info without token fails."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_get_me_invalid_token(self, client):
        """Test getting current user info with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401
