import pytest

from app.exceptions import (
    InactiveUserException,
    InvalidPasswordException,
    UserNotFoundException,
)
from app.models.user import LoginRequest, UserCreate
from app.services.user import UserService


class TestLoginUser:
    async def test_login_exitoso(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        await service.create.execute(user_data)

        token_response = await service.login.execute(
            LoginRequest(email=user_data.email, password=user_data.password)
        )

        assert token_response.access_token is not None
        assert token_response.token_type == "bearer"

    async def test_login_usuario_no_existe(self, service: UserService):
        with pytest.raises(UserNotFoundException):
            await service.login.execute(
                LoginRequest(email="noexiste@test.com", password="Password123")
            )

    async def test_login_password_incorrecta(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        await service.create.execute(user_data)

        with pytest.raises(InvalidPasswordException):
            await service.login.execute(
                LoginRequest(email=user_data.email, password="WrongPassword")
            )

    async def test_login_usuario_inactivo(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)
        await service.delete.execute(user)

        with pytest.raises(InactiveUserException):
            await service.login.execute(
                LoginRequest(email=user_data.email, password=user_data.password)
            )
