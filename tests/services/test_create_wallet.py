import pytest

from app.exceptions import InactiveUserException, WalletAlreadyExistsException
from app.models.user import User
from app.services.wallet import WalletService


class TestCreateWallet:
    async def test_create_wallet_exitoso(
        self, wallet_service: WalletService, created_user: User
    ):
        wallet = await wallet_service.create.execute(created_user)

        assert wallet.id is not None
        assert wallet.user_id == created_user.id
        assert wallet.balance == 0
        assert wallet.is_active is True

    async def test_create_wallet_duplicado(
        self, wallet_service: WalletService, created_user: User
    ):
        await wallet_service.create.execute(created_user)

        with pytest.raises(WalletAlreadyExistsException):
            await wallet_service.create.execute(created_user)

    async def test_create_wallet_usuario_inactivo(
        self, wallet_service: WalletService, inactive_user: User
    ):
        with pytest.raises(InactiveUserException):
            await wallet_service.create.execute(inactive_user)
