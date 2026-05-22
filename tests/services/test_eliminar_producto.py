from app.models.user import LoginRequest, UserCreate
from app.services.user import UserService
from app.exceptions import InactiveUserException
import pytest


class TestDeleteUser:
    async def test_delete_desactiva_usuario(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)
        assert user.is_active is True

        deactivated = await service.delete.execute(user)

        assert deactivated.is_active is False

    async def test_token_invalido_despues_de_delete(
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

    async def test_delete_actualiza_updated_at(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)
        original_updated_at = user.updated_at

        deactivated = await service.delete.execute(user)

        assert deactivated.updated_at >= original_updated_at
