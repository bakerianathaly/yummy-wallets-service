from decimal import Decimal
from uuid import UUID

from app.exceptions import (
    InactiveWalletException,
    InsufficientFundsException,
    InvalidAmountException,
    SameWalletTransferException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import Transaction, TransferRequest
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository

MIN_TRANSFER = Decimal("0.5")


class TransferWallet:
    def __init__(self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository):
        self.wallet_repo = wallet_repo
        self.transaction_repo = transaction_repo

    async def execute(self, from_wallet_id: UUID, user: User, request: TransferRequest) -> Transaction:
        if request.amount <= Decimal("0"):
            raise InvalidAmountException("El monto debe ser positivo")
        if request.amount < MIN_TRANSFER:
            raise InvalidAmountException(f"El monto mínimo de transferencia es {MIN_TRANSFER}")
        if from_wallet_id == request.to_wallet_id:
            raise SameWalletTransferException("No puedes transferir a tu propia wallet")

        existing = await self.transaction_repo.get_by_idempotency_key(request.idempotency_key)
        if existing:
            return existing

        # Bloqueamos ambas wallets en orden ascendente de UUID para prevenir deadlock.
        #
        # Si no hiciéramos esto y llegaran A→B y B→A al mismo tiempo, cada request
        # bloquearía "su" wallet primero y esperaría la del otro indefinidamente.
        # Al ordenar siempre igual, ambas requests compiten por el mismo lock primero
        # y una espera a la otra sin bloquearse mutuamente.
        first_id, second_id = sorted([from_wallet_id, request.to_wallet_id])
        wallet_first = await self.wallet_repo.get_by_id_for_update(first_id)
        wallet_second = await self.wallet_repo.get_by_id_for_update(second_id)

        # Recuperamos cuál es origen y cuál destino sin importar el orden en que los bloqueamos.
        if first_id == from_wallet_id:
            from_wallet, to_wallet = wallet_first, wallet_second
        else:
            from_wallet, to_wallet = wallet_second, wallet_first

        if from_wallet is None:
            raise WalletNotFoundException("Wallet de origen no encontrada")
        if from_wallet.user_id != user.id:
            raise UnauthorizedWalletAccessException("No tienes acceso a la wallet de origen")
        if to_wallet is None:
            raise WalletNotFoundException("Wallet de destino no encontrada")
        if not to_wallet.is_active:
            raise InactiveWalletException("La wallet de destino está desactivada")
        if from_wallet.balance < request.amount:
            raise InsufficientFundsException(
                f"Saldo insuficiente. Balance actual: {from_wallet.balance}, monto solicitado: {request.amount}"
            )

        new_from_balance = from_wallet.balance - request.amount
        new_to_balance = to_wallet.balance + request.amount

        # Ambos update_balance hacen flush (no commit), así que quedan dentro de la
        # misma transacción de DB. El commit ocurre una sola vez en save_transfer_pair.
        await self.wallet_repo.update_balance(from_wallet, new_from_balance)
        await self.wallet_repo.update_balance(to_wallet, new_to_balance)

        tx_out = Transaction(
            wallet_id=from_wallet.id,
            type="transfer_out",
            amount=request.amount,
            balance_after=new_from_balance,
            idempotency_key=request.idempotency_key,
            description=request.description,
        )
        tx_in = Transaction(
            wallet_id=to_wallet.id,
            type="transfer_in",
            amount=request.amount,
            balance_after=new_to_balance,
            description=request.description,
        )

        tx_out, _ = await self.transaction_repo.save_transfer_pair(tx_out, tx_in)
        return tx_out
