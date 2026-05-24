"""
Tests para GetWalletSummary — el endpoint que devuelve saldo + últimas 10 transacciones.
Inspirado en la pantalla principal de Zinli: una sola llamada trae todo lo que necesita la home.
"""

import pytest
from decimal import Decimal

from app.exceptions import WalletNotFoundException
from app.models.wallet import Transaction
from app.services.wallet.get_wallet_summary import GetWalletSummary
from app.repositories.wallet_repository import WalletRepository
from app.repositories.transaction_repository import TransactionRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.wallet import Wallet


@pytest.fixture
def summary_service(
    wallet_repo: WalletRepository, transaction_repo: TransactionRepository
) -> GetWalletSummary:
    return GetWalletSummary(wallet_repo, transaction_repo)


# ─── Sin wallet ───────────────────────────────────────────────


async def test_usuario_sin_wallet_lanza_excepcion(
    summary_service: GetWalletSummary, created_user: User
):
    # El usuario existe pero nunca creó una wallet — debe fallar limpiamente.
    with pytest.raises(WalletNotFoundException):
        await summary_service.execute(created_user)


# ─── Wallet sin transacciones ─────────────────────────────────


async def test_wallet_sin_transacciones_devuelve_lista_vacia(
    summary_service: GetWalletSummary, created_user: User, created_wallet: Wallet
):
    result = await summary_service.execute(created_user)

    assert result.balance == Decimal("0")
    assert result.recent_transactions == []


async def test_balance_correcto_en_summary(
    summary_service: GetWalletSummary,
    wallet_repo: WalletRepository,
    created_user: User,
    created_wallet: Wallet,
):
    # Actualizamos el balance directamente para simular que hubo depósitos previos.
    await wallet_repo.update_balance(created_wallet, Decimal("250.50"))

    result = await summary_service.execute(created_user)

    assert result.balance == Decimal("250.50")


async def test_is_active_y_created_at_presentes(
    summary_service: GetWalletSummary, created_user: User, created_wallet: Wallet
):
    result = await summary_service.execute(created_user)

    assert result.is_active is True
    assert result.created_at is not None
    assert result.id == created_wallet.id


# ─── Con transacciones ────────────────────────────────────────


async def test_transacciones_ordenadas_mas_reciente_primero(
    summary_service: GetWalletSummary,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    # Insertamos 3 transacciones con fechas explícitas para verificar el orden.
    from datetime import datetime, timedelta

    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(3):
        tx = Transaction(
            wallet_id=created_wallet.id,
            type="deposit",
            amount=Decimal("10"),
            balance_after=Decimal(str(10 * (i + 1))),
            idempotency_key=f"order-key-{i}",
            created_at=base + timedelta(hours=i),
        )
        db_session.add(tx)
    await db_session.commit()

    result = await summary_service.execute(created_user)

    fechas = [tx.created_at for tx in result.recent_transactions]
    assert fechas == sorted(fechas, reverse=True), (
        "Las transacciones deben venir de más reciente a más antigua"
    )


async def test_maximo_10_transacciones_en_summary(
    summary_service: GetWalletSummary,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    # El usuario tiene 15 transacciones. La home solo debe mostrar las 10 más recientes.
    for i in range(15):
        tx = Transaction(
            wallet_id=created_wallet.id,
            type="deposit",
            amount=Decimal("1"),
            balance_after=Decimal(str(i + 1)),
            idempotency_key=f"limit-key-{i}",
        )
        db_session.add(tx)
    await db_session.commit()

    result = await summary_service.execute(created_user)

    assert len(result.recent_transactions) == 10


async def test_con_exactamente_10_transacciones_devuelve_todas(
    summary_service: GetWalletSummary,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    for i in range(10):
        tx = Transaction(
            wallet_id=created_wallet.id,
            type="deposit",
            amount=Decimal("1"),
            balance_after=Decimal(str(i + 1)),
            idempotency_key=f"exact-key-{i}",
        )
        db_session.add(tx)
    await db_session.commit()

    result = await summary_service.execute(created_user)

    assert len(result.recent_transactions) == 10


async def test_con_menos_de_10_transacciones_devuelve_todas(
    summary_service: GetWalletSummary,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    for i in range(4):
        tx = Transaction(
            wallet_id=created_wallet.id,
            type="deposit",
            amount=Decimal("5"),
            balance_after=Decimal(str(5 * (i + 1))),
            idempotency_key=f"few-key-{i}",
        )
        db_session.add(tx)
    await db_session.commit()

    result = await summary_service.execute(created_user)

    assert len(result.recent_transactions) == 4


async def test_campos_de_transaccion_presentes_en_respuesta(
    summary_service: GetWalletSummary,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    tx = Transaction(
        wallet_id=created_wallet.id,
        type="deposit",
        amount=Decimal("100"),
        balance_after=Decimal("100"),
        idempotency_key="fields-check-key",
        description="Depósito de prueba",
    )
    db_session.add(tx)
    await db_session.commit()

    result = await summary_service.execute(created_user)

    tx_resp = result.recent_transactions[0]
    assert tx_resp.type == "deposit"
    assert tx_resp.amount == Decimal("100")
    assert tx_resp.balance_after == Decimal("100")
    assert tx_resp.description == "Depósito de prueba"
    assert tx_resp.created_at is not None
