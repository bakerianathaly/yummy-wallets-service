import pytest

from app.exceptions import (
    InactiveUserException,
    UserAlreadyExistsException,
    ValidationException,
)
from app.models.user import UserCreate, UserUpdate
from app.services.user.user_service import UserService


class TestUpdateUser:
    async def test_update_full_name(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        updated = await service.update.execute(
            user, UserUpdate(full_name="Nuevo Nombre")
        )

        assert updated.full_name == "Nuevo Nombre"
        assert updated.email == user.email

    async def test_update_email(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        updated = await service.update.execute(
            user, UserUpdate(email="nuevo@yummy.com")
        )

        assert updated.email == "nuevo@yummy.com"

    async def test_update_password(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        updated = await service.update.execute(
            user, UserUpdate(password="NuevaPassword123")
        )

        assert updated.hashed_password != user_data.password

    async def test_update_email_duplicado(
        self,
        service: UserService,
        user_data: UserCreate,
        user_data_2: UserCreate,
    ):
        user1 = await service.create.execute(user_data)
        await service.create.execute(user_data_2)

        with pytest.raises(UserAlreadyExistsException):
            await service.update.execute(user1, UserUpdate(email=user_data_2.email))

    async def test_update_usuario_inactivo(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)
        await service.delete.execute(user)

        with pytest.raises(InactiveUserException):
            await service.update.execute(user, UserUpdate(full_name="Nuevo"))

    async def test_update_password_corta(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        with pytest.raises(ValidationException) as exc:
            await service.update.execute(user, UserUpdate(password="short"))

        assert "contraseña" in str(exc.value).lower()

    async def test_update_email_invalido(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        with pytest.raises(ValidationException) as exc:
            await service.update.execute(user, UserUpdate(email="no-es-email"))

        assert "email" in str(exc.value).lower()
