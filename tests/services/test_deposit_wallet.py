from decimal import Decimal
from uuid import uuid4

import pytest

from app.exceptions import (
    InvalidAmountException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import DepositRequest, Wallet
from app.services.wallet import WalletService


def _request(amount: str, key: str = "idem-key-1") -> DepositRequest:
    return DepositRequest(amount=Decimal(amount), idempotency_key=key)


class TestDepositWallet:
    async def test_deposito_exitoso(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        transaction = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("100")
        )

        assert transaction.type == "deposit"
        assert transaction.amount == Decimal("100")
        assert transaction.balance_after == Decimal("100")
        assert transaction.wallet_id == created_wallet.id

    async def test_balance_acumulado(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("50", "k1")
        )
        t2 = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("30", "k2")
        )

        assert t2.balance_after == Decimal("80")

    async def test_monto_minimo_exacto_valido(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        transaction = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("0.5")
        )

        assert transaction.amount == Decimal("0.5")

    async def test_monto_por_debajo_del_minimo(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        with pytest.raises(InvalidAmountException):
            await wallet_service.deposit.execute(
                created_wallet.id, created_user, _request("0.4")
            )

    async def test_monto_cero_rechazado(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        with pytest.raises(InvalidAmountException):
            await wallet_service.deposit.execute(
                created_wallet.id, created_user, _request("0")
            )

    async def test_monto_negativo_rechazado(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        with pytest.raises(InvalidAmountException):
            await wallet_service.deposit.execute(
                created_wallet.id, created_user, _request("-10")
            )

    async def test_wallet_no_encontrada(
        self, wallet_service: WalletService, created_user: User
    ):
        with pytest.raises(WalletNotFoundException):
            await wallet_service.deposit.execute(uuid4(), created_user, _request("100"))

    async def test_wallet_de_otro_usuario(
        self, wallet_service: WalletService, another_user: User, created_wallet: Wallet
    ):
        with pytest.raises(UnauthorizedWalletAccessException):
            await wallet_service.deposit.execute(
                created_wallet.id, another_user, _request("100")
            )

    async def test_idempotencia_retorna_transaccion_existente(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        first = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("100", "same-key")
        )
        second = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("100", "same-key")
        )

        assert first.id == second.id

    async def test_idempotencia_no_duplica_saldo(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("100", "same-key")
        )
        second = await wallet_service.deposit.execute(
            created_wallet.id, created_user, _request("100", "same-key")
        )

        assert second.balance_after == Decimal("100")
