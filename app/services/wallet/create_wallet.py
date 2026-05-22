from app.exceptions import InactiveUserException, WalletAlreadyExistsException
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.wallet_repository import WalletRepository


class CreateWallet:
    def __init__(self, repository: WalletRepository):
        self.repository = repository

    async def execute(self, user: User) -> Wallet:
        if not user.is_active:
            raise InactiveUserException("El usuario está desactivado")

        existing = await self.repository.get_by_user_id(user.id)
        if existing:
            raise WalletAlreadyExistsException(
                f"El usuario ya tiene un wallet registrado"
            )

        wallet = Wallet(user_id=user.id)
        return await self.repository.create(wallet)
