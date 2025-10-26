# tests/test_users.py

from typing import Dict
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import get_user_by_email
from app.auth import verify_password

class TestUserRegistration:
    async def test_register_user_success(self, client: AsyncClient, test_user_data: Dict[str, str]) -> None:
        """Test successful user registration."""
        response = await client.post("/register", json=test_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["name"] == test_user_data["name"]
        assert "id" in data
        assert "created_at" in data

    async def test_register_user_duplicate_email(self, client: AsyncClient, test_user_data: Dict[str, str]) -> None:
        """Test registration with duplicate email fails."""
        # Register first user
        await client.post("/register", json=test_user_data)

        # Try to register again with same email
        response = await client.post("/register", json=test_user_data)

        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    async def test_register_user_invalid_email(self, client: AsyncClient) -> None:
        """Test registration with invalid email fails."""
        invalid_user_data = {
            "email": "invalid-email",
            "name": "Test User",
            "password": "testpassword123"
        }

        response = await client.post("/register", json=invalid_user_data)

        assert response.status_code == 422  # Validation error

    async def test_register_user_password_too_long(self, client: AsyncClient) -> None:
        """Test registration with password exceeding 72 bytes fails."""
        long_password_data = {
            "email": "test@example.com",
            "name": "Test User",
            "password": "a" * 73  # 73 characters, exceeds 72 bytes
        }

        response = await client.post("/register", json=long_password_data)

        assert response.status_code == 422  # Validation error

class TestUserLogin:
    async def test_login_success(self, client: AsyncClient, test_user_data: Dict[str, str]) -> None:
        """Test successful login."""
        # First register the user
        await client.post("/register", json=test_user_data)

        # Now login
        login_data = {
            "username": test_user_data["email"],  # OAuth2 form uses 'username'
            "password": test_user_data["password"]
        }

        response = await client.post("/token", data=login_data)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data: Dict[str, str]) -> None:
        """Test login with wrong password fails."""
        # First register the user
        await client.post("/register", json=test_user_data)

        # Try login with wrong password
        login_data = {
            "username": test_user_data["email"],
            "password": "wrongpassword"
        }

        response = await client.post("/token", data=login_data)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        """Test login with nonexistent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }

        response = await client.post("/token", data=login_data)

        assert response.status_code == 400
        assert "Incorrect email or password" in response.json()["detail"]

class TestUserDatabaseOperations:
    async def test_user_created_in_database(self, client: AsyncClient, test_session: AsyncSession, test_user_data: Dict[str, str]) -> None:
        """Test that user is properly stored in database after registration."""
        response = await client.post("/register", json=test_user_data)
        assert response.status_code == 200

        # Check database
        user = await get_user_by_email(test_session, test_user_data["email"])
        assert user is not None
        assert user.email == test_user_data["email"]
        assert user.name == test_user_data["name"]
        assert not verify_password("wrongpassword", user.hashed_password)  # Wrong password should fail
        assert verify_password(test_user_data["password"], user.hashed_password)  # Correct password should work