from decimal import Decimal
from uuid import uuid4

import pytest

from app.exceptions import (
    InsufficientFundsException,
    InvalidAmountException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import DepositRequest, Wallet, WithdrawalRequest
from app.services.wallet import WalletService


def _deposit(amount: str, key: str) -> DepositRequest:
    return DepositRequest(amount=Decimal(amount), idempotency_key=key)


def _withdraw(amount: str, key: str = "withdraw-key-1") -> WithdrawalRequest:
    return WithdrawalRequest(amount=Decimal(amount), idempotency_key=key)


async def _funded_wallet(
    wallet_service: WalletService, wallet: Wallet, user: User, amount: str = "100"
) -> None:
    await wallet_service.deposit.execute(wallet.id, user, _deposit(amount, f"fund-{amount}"))


class TestWithdrawWallet:
    async def test_retiro_exitoso(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user)

        transaction = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("30")
        )

        assert transaction.type == "withdrawal"
        assert transaction.amount == Decimal("30")
        assert transaction.balance_after == Decimal("70")
        assert transaction.wallet_id == created_wallet.id

    async def test_balance_acumulado_retiros(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user, "100")

        await wallet_service.withdraw.execute(created_wallet.id, created_user, _withdraw("20", "k1"))
        t2 = await wallet_service.withdraw.execute(created_wallet.id, created_user, _withdraw("15", "k2"))

        assert t2.balance_after == Decimal("65")

    async def test_monto_minimo_exacto_valido(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user)

        transaction = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("0.5")
        )

        assert transaction.amount == Decimal("0.5")

    async def test_monto_por_debajo_del_minimo(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user)

        with pytest.raises(InvalidAmountException):
            await wallet_service.withdraw.execute(
                created_wallet.id, created_user, _withdraw("0.49")
            )

    async def test_monto_cero_rechazado(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user)

        with pytest.raises(InvalidAmountException):
            await wallet_service.withdraw.execute(
                created_wallet.id, created_user, _withdraw("0")
            )

    async def test_monto_negativo_rechazado(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user)

        with pytest.raises(InvalidAmountException):
            await wallet_service.withdraw.execute(
                created_wallet.id, created_user, _withdraw("-10")
            )

    async def test_saldo_insuficiente(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user, "10")

        with pytest.raises(InsufficientFundsException):
            await wallet_service.withdraw.execute(
                created_wallet.id, created_user, _withdraw("20")
            )

    async def test_saldo_exacto_valido(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user, "50")

        transaction = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("50")
        )

        assert transaction.balance_after == Decimal("0")

    async def test_wallet_no_encontrada(
        self, wallet_service: WalletService, created_user: User
    ):
        with pytest.raises(WalletNotFoundException):
            await wallet_service.withdraw.execute(
                uuid4(), created_user, _withdraw("10")
            )

    async def test_wallet_de_otro_usuario(
        self, wallet_service: WalletService, another_user: User, created_wallet: Wallet
    ):
        with pytest.raises(UnauthorizedWalletAccessException):
            await wallet_service.withdraw.execute(
                created_wallet.id, another_user, _withdraw("10")
            )

    async def test_idempotencia_retorna_transaccion_existente(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user, "100")

        first = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("30", "same-key")
        )
        second = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("30", "same-key")
        )

        assert first.id == second.id

    async def test_idempotencia_no_duplica_saldo(
        self, wallet_service: WalletService, created_user: User, created_wallet: Wallet
    ):
        await _funded_wallet(wallet_service, created_wallet, created_user, "100")

        await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("30", "same-key")
        )
        second = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("30", "same-key")
        )

        # El balance sigue siendo 70, no 40
        assert second.balance_after == Decimal("70")
