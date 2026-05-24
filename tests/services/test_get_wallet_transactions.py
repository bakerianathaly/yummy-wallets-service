"""
Tests para GetWalletTransactions — historial paginado completo.
Cuando el usuario quiere ver más allá de las últimas 10 de la home, usa este endpoint.
"""

import pytest
from decimal import Decimal

from app.exceptions import WalletNotFoundException
from app.models.wallet import Transaction
from app.services.wallet.get_wallet_transactions import GetWalletTransactions
from app.repositories.wallet_repository import WalletRepository
from app.repositories.transaction_repository import TransactionRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.wallet import Wallet


@pytest.fixture
def transactions_service(
    wallet_repo: WalletRepository, transaction_repo: TransactionRepository
) -> GetWalletTransactions:
    return GetWalletTransactions(wallet_repo, transaction_repo)


async def _crear_transacciones(db_session: AsyncSession, wallet_id, cantidad: int):
    """Helper que inserta N transacciones de depósito para un wallet dado."""
    for i in range(cantidad):
        tx = Transaction(
            wallet_id=wallet_id,
            type="deposit",
            amount=Decimal("10"),
            balance_after=Decimal(str(10 * (i + 1))),
            idempotency_key=f"paginate-key-{wallet_id}-{i}",
        )
        db_session.add(tx)
    await db_session.commit()


# ─── Sin wallet ───────────────────────────────────────────────


async def test_usuario_sin_wallet_lanza_excepcion(
    transactions_service: GetWalletTransactions, created_user: User
):
    with pytest.raises(WalletNotFoundException):
        await transactions_service.execute(created_user, page=1, page_size=20)


# ─── Sin transacciones ────────────────────────────────────────


async def test_sin_transacciones_devuelve_paginacion_vacia(
    transactions_service: GetWalletTransactions,
    created_user: User,
    created_wallet: Wallet,
):
    result = await transactions_service.execute(created_user, page=1, page_size=20)

    assert result.transactions == []
    assert result.total == 0
    assert result.total_pages == 1  # sin datos, igual existe la "página 1"
    assert result.page == 1
    assert result.page_size == 20


# ─── Paginación correcta ──────────────────────────────────────


async def test_primera_pagina_devuelve_page_size_items(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    await _crear_transacciones(db_session, created_wallet.id, 25)

    result = await transactions_service.execute(created_user, page=1, page_size=10)

    assert len(result.transactions) == 10
    assert result.total == 25
    assert result.total_pages == 3


async def test_segunda_pagina_devuelve_siguiente_bloque(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    await _crear_transacciones(db_session, created_wallet.id, 25)

    pagina_1 = await transactions_service.execute(created_user, page=1, page_size=10)
    pagina_2 = await transactions_service.execute(created_user, page=2, page_size=10)

    ids_pagina_1 = {tx.id for tx in pagina_1.transactions}
    ids_pagina_2 = {tx.id for tx in pagina_2.transactions}

    # Las dos páginas no deben tener ningún elemento en común.
    assert ids_pagina_1.isdisjoint(ids_pagina_2), "Páginas distintas no deben solaparse"


async def test_ultima_pagina_con_items_residuales(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    # 25 items con page_size=10 → la página 3 tiene solo 5.
    await _crear_transacciones(db_session, created_wallet.id, 25)

    result = await transactions_service.execute(created_user, page=3, page_size=10)

    assert len(result.transactions) == 5
    assert result.total == 25


async def test_pagina_fuera_de_rango_devuelve_lista_vacia(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    await _crear_transacciones(db_session, created_wallet.id, 5)

    result = await transactions_service.execute(created_user, page=99, page_size=10)

    assert result.transactions == []
    assert result.total == 5


# ─── Orden y metadatos ────────────────────────────────────────


async def test_transacciones_ordenadas_mas_reciente_primero(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    from datetime import datetime, timedelta

    base = datetime(2026, 1, 1, 12, 0, 0)
    for i in range(5):
        tx = Transaction(
            wallet_id=created_wallet.id,
            type="deposit",
            amount=Decimal("10"),
            balance_after=Decimal(str(10 * (i + 1))),
            idempotency_key=f"order-pag-key-{i}",
            created_at=base + timedelta(hours=i),
        )
        db_session.add(tx)
    await db_session.commit()

    result = await transactions_service.execute(created_user, page=1, page_size=10)

    fechas = [tx.created_at for tx in result.transactions]
    assert fechas == sorted(fechas, reverse=True)


async def test_total_pages_calculado_correctamente(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    await _crear_transacciones(db_session, created_wallet.id, 21)

    result = await transactions_service.execute(created_user, page=1, page_size=10)

    # 21 items / 10 por página = 3 páginas (ceil)
    assert result.total_pages == 3


async def test_page_size_maximo_respetado(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    # El servicio clampea page_size al máximo de 100 si el cliente manda un valor mayor.
    await _crear_transacciones(db_session, created_wallet.id, 10)

    result = await transactions_service.execute(created_user, page=1, page_size=999)

    assert result.page_size == 100


async def test_page_minimo_es_1(
    transactions_service: GetWalletTransactions,
    db_session: AsyncSession,
    created_user: User,
    created_wallet: Wallet,
):
    # Si el cliente manda page=0 o negativo, el servicio lo normaliza a 1.
    await _crear_transacciones(db_session, created_wallet.id, 3)

    result = await transactions_service.execute(created_user, page=0, page_size=10)

    assert result.page == 1
    assert len(result.transactions) == 3
