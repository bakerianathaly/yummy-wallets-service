from uuid import uuid4

from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository


class TestWalletRepository:
    async def test_create_wallet(self, wallet_repo: WalletRepository, created_user: User):
        wallet = Wallet(user_id=created_user.id)
        created = await wallet_repo.create(wallet)

        assert created.id is not None
        assert created.user_id == created_user.id
        assert created.balance == 0
        assert created.is_active is True

    async def test_get_by_user_id_existente(
        self, wallet_repo: WalletRepository, created_user: User
    ):
        wallet = await wallet_repo.create(Wallet(user_id=created_user.id))

        found = await wallet_repo.get_by_user_id(created_user.id)

        assert found is not None
        assert found.id == wallet.id

    async def test_get_by_user_id_inexistente(self, wallet_repo: WalletRepository):
        found = await wallet_repo.get_by_user_id(uuid4())

        assert found is None

    async def test_get_by_id_existente(
        self, wallet_repo: WalletRepository, created_user: User
    ):
        wallet = await wallet_repo.create(Wallet(user_id=created_user.id))

        found = await wallet_repo.get_by_id(wallet.id)

        assert found is not None
        assert found.id == wallet.id

    async def test_get_by_id_inexistente(self, wallet_repo: WalletRepository):
        found = await wallet_repo.get_by_id(uuid4())

        assert found is None
