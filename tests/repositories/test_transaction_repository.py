from decimal import Decimal
from uuid import uuid4

from app.models.wallet import Transaction, Wallet
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository


def _make_transaction(wallet_id, idempotency_key="key-1") -> Transaction:
    return Transaction(
        wallet_id=wallet_id,
        type="deposit",
        amount=Decimal("100"),
        balance_after=Decimal("100"),
        idempotency_key=idempotency_key,
    )


class TestTransactionRepository:
    async def test_create(
        self, transaction_repo: TransactionRepository, created_wallet: Wallet
    ):
        transaction = _make_transaction(created_wallet.id)
        created = await transaction_repo.create(transaction)

        assert created.id is not None
        assert created.wallet_id == created_wallet.id
        assert created.type == "deposit"
        assert created.amount == Decimal("100")
        assert created.balance_after == Decimal("100")

    async def test_get_by_idempotency_key_existente(
        self, transaction_repo: TransactionRepository, created_wallet: Wallet
    ):
        await transaction_repo.create(_make_transaction(created_wallet.id, "unique-key"))

        found = await transaction_repo.get_by_idempotency_key("unique-key")

        assert found is not None
        assert found.idempotency_key == "unique-key"

    async def test_get_by_idempotency_key_inexistente(
        self, transaction_repo: TransactionRepository
    ):
        found = await transaction_repo.get_by_idempotency_key("no-existe")

        assert found is None

    async def test_get_by_wallet_id_con_transacciones(
        self, transaction_repo: TransactionRepository, created_wallet: Wallet
    ):
        await transaction_repo.create(_make_transaction(created_wallet.id, "k1"))
        await transaction_repo.create(_make_transaction(created_wallet.id, "k2"))

        results = await transaction_repo.get_by_wallet_id(created_wallet.id)

        assert len(results) == 2

    async def test_get_by_wallet_id_sin_transacciones(
        self, transaction_repo: TransactionRepository, created_wallet: Wallet
    ):
        results = await transaction_repo.get_by_wallet_id(created_wallet.id)

        assert results == []

    async def test_get_by_wallet_id_otra_wallet(
        self, transaction_repo: TransactionRepository, created_wallet: Wallet
    ):
        await transaction_repo.create(_make_transaction(created_wallet.id, "k1"))

        results = await transaction_repo.get_by_wallet_id(uuid4())

        assert results == []
