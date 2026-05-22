import pytest

from app.exceptions import UserAlreadyExistsException, ValidationException
from app.models.user import UserCreate
from app.services.user import UserService


class TestCreateUser:
    async def test_create_user_exitoso(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        user = await service.create.execute(user_data)

        assert user.id is not None
        assert user.email == user_data.email.lower().strip()
        assert user.full_name == user_data.full_name.strip()
        assert user.is_active is True

    async def test_create_user_email_duplicado(
        self,
        service: UserService,
        user_data: UserCreate,
    ):
        await service.create.execute(user_data)

        with pytest.raises(UserAlreadyExistsException):
            await service.create.execute(user_data)

    async def test_create_user_email_invalido(self, service: UserService):
        data = UserCreate(email="no-es-email", full_name="Test", password="Password123")

        with pytest.raises(ValidationException) as exc:
            await service.create.execute(data)

        assert "email" in str(exc.value).lower()

    async def test_create_user_password_corta(self, service: UserService):
        data = UserCreate(email="test@test.com", full_name="Test", password="short")

        with pytest.raises(ValidationException) as exc:
            await service.create.execute(data)

        assert "contraseña" in str(exc.value).lower()

    async def test_create_user_nombre_corto(self, service: UserService):
        data = UserCreate(email="test@test.com", full_name="A", password="Password123")

        with pytest.raises(ValidationException) as exc:
            await service.create.execute(data)

        assert "nombre" in str(exc.value).lower()

    async def test_create_user_email_normalizado(self, service: UserService):
        data = UserCreate(
            email="  TEST@YUMMY.COM  ",
            full_name="Test User",
            password="Password123",
        )

        user = await service.create.execute(data)

        assert user.email == "test@yummy.com"
