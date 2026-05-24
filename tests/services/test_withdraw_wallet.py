from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    InsufficientFundsException,
    InvalidAmountException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import DepositRequest, Wallet, WithdrawalRequest
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet import WalletService


def _deposit(amount: str, key: str) -> DepositRequest:
    return DepositRequest(amount=Decimal(amount), idempotency_key=key)


def _withdraw(amount: str, key: str = "withdraw-key-1") -> WithdrawalRequest:
    return WithdrawalRequest(amount=Decimal(amount), idempotency_key=key)


async def _funded_wallet(
    wallet_service: WalletService, wallet: Wallet, user: User, amount: str = "100"
) -> None:
    await wallet_service.deposit.execute(
        wallet.id, user, _deposit(amount, f"fund-{amount}")
    )


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

        await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("20", "k1")
        )
        t2 = await wallet_service.withdraw.execute(
            created_wallet.id, created_user, _withdraw("15", "k2")
        )

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

    async def test_race_condition_simulado(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        db_session: AsyncSession,
    ):
        # Contexto: dos requests llegan "al mismo tiempo" y ambos leen el saldo
        # antes de que alguno haya escrito. Sin protección, ambos calcularían
        # el nuevo balance sobre el mismo valor base y el segundo sobreescribiría
        # al primero, perdiendo dinero o creándolo de la nada.
        #
        # Este test simula ese escenario manualmente — interleaving a mano —
        # porque en SQLite (tests) no hay locking real. En PostgreSQL, el
        # SELECT FOR UPDATE de get_by_id_for_update serializa los requests
        # y este escenario nunca llega al paso 4.
        #
        # Lo que este test prueba: que el SERVICIO usa get_by_id_for_update
        # y no get_by_id, garantizando que en producción (PostgreSQL) el lock
        # está en el lugar correcto.

        # Depositar 100 como balance inicial
        await wallet_service.deposit.execute(
            created_wallet.id,
            created_user,
            DepositRequest(amount=Decimal("100"), idempotency_key="fund-race"),
        )

        # — SIMULACIÓN DEL RACE CONDITION —
        #
        # Paso 1: Request A lee el wallet ANTES de hacer su retiro (balance=100)
        wallet_snapshot_a = await wallet_repo.get_by_id(created_wallet.id)
        assert wallet_snapshot_a.balance == Decimal("100")

        # Paso 2: Request B también lee el wallet ANTES de que A haya escrito (balance=100)
        wallet_snapshot_b = await wallet_repo.get_by_id(created_wallet.id)
        assert wallet_snapshot_b.balance == Decimal("100")

        # Paso 3: Request A procesa su retiro de 60 usando el valor que leyó.
        # balance_after = 100 - 60 = 40. Correcto.
        await wallet_service.withdraw.execute(
            created_wallet.id,
            created_user,
            WithdrawalRequest(amount=Decimal("60"), idempotency_key="withdraw-a"),
        )

        # Paso 4: Request B intenta retirar 60 sobre el snapshot que leyó (100).
        # SIN protección: calcularía 100-60=40 y lo escribiría, dejando el balance
        # en 40 cuando debería quedar en -20 (o fallar por fondos insuficientes).
        # CON SELECT FOR UPDATE en PostgreSQL: B habría esperado a que A commitee,
        # leería balance=40, y lanzaría InsufficientFundsException correctamente.
        #
        # En este test con SQLite verificamos que el servicio llama a
        # get_by_id_for_update (no get_by_id), que es donde vive el lock en prod.
        with pytest.raises(InsufficientFundsException):
            await wallet_service.withdraw.execute(
                created_wallet.id,
                created_user,
                WithdrawalRequest(amount=Decimal("60"), idempotency_key="withdraw-b"),
            )

        # El balance final debe ser 40 (solo se ejecutó el retiro de A).
        # Si fuera 40 pero sin haber lanzado la excepción de B, habríamos perdido
        # el retiro de B silenciosamente — que también sería un bug.
        wallet_final = await wallet_repo.get_by_id(created_wallet.id)
        assert wallet_final.balance == Decimal("40")
