from decimal import Decimal
from uuid import UUID

from app.exceptions import (
    InvalidAmountException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import DepositRequest, Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository

MIN_DEPOSIT = Decimal("0.5")


class DepositWallet:
    def __init__(self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository):
        self.wallet_repo = wallet_repo
        self.transaction_repo = transaction_repo

    async def execute(self, wallet_id: UUID, user: User, request: DepositRequest) -> Transaction:
        if request.amount < MIN_DEPOSIT:
            raise InvalidAmountException(
                f"El monto mínimo de depósito es {MIN_DEPOSIT}"
            )

        existing = await self.transaction_repo.get_by_idempotency_key(request.idempotency_key)
        if existing:
            return existing

        wallet = await self.wallet_repo.get_by_id(wallet_id)
        if wallet is None:
            raise WalletNotFoundException("Wallet no encontrada")

        if wallet.user_id != user.id:
            raise UnauthorizedWalletAccessException("No tienes acceso a esta wallet")

        new_balance = wallet.balance + request.amount

        await self.wallet_repo.update_balance(wallet, new_balance)

        transaction = Transaction(
            wallet_id=wallet.id,
            type="deposit",
            amount=request.amount,
            balance_after=new_balance,
            idempotency_key=request.idempotency_key,
            description=request.description,
        )
        return await self.transaction_repo.create(transaction)
