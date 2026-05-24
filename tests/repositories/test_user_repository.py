from uuid import uuid4


from app.models.user import UserCreate
from app.repositories.user_repository import UserRepository
from app.models.user import User


class TestUserRepository:
    async def test_create_user(
        self,
        repo: UserRepository,
        user_data: UserCreate,
    ):
        user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password="hashed",
        )
        created = await repo.create(user)

        assert created.id is not None
        assert created.email == user_data.email
        assert created.full_name == user_data.full_name
        assert created.is_active is True

    async def test_get_by_id_existente(
        self, repo: UserRepository, user_data: UserCreate
    ):
        user = await repo.create(
            User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password="h",
            )
        )

        found = await repo.get_by_id(user.id)

        assert found is not None
        assert found.id == user.id

    async def test_get_by_id_inexistente(self, repo: UserRepository):
        found = await repo.get_by_id(uuid4())

        assert found is None

    async def test_get_by_email_existente(
        self, repo: UserRepository, user_data: UserCreate
    ):
        await repo.create(
            User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password="h",
            )
        )

        found = await repo.get_by_email(user_data.email)

        assert found is not None
        assert found.email == user_data.email

    async def test_get_by_email_inexistente(self, repo: UserRepository):
        found = await repo.get_by_email("noexiste@test.com")

        assert found is None

    async def test_update_user(self, repo: UserRepository, user_data: UserCreate):
        user = await repo.create(
            User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password="h",
            )
        )
        user.full_name = "Nombre Actualizado"

        updated = await repo.update(user)

        assert updated.full_name == "Nombre Actualizado"

    async def test_deactivate_user(self, repo: UserRepository, user_data: UserCreate):
        user = await repo.create(
            User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password="h",
            )
        )
        user.is_active = False

        updated = await repo.update(user)

        assert updated.is_active is False
