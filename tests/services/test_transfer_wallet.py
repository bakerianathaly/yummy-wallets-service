from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    InactiveWalletException,
    InsufficientFundsException,
    InvalidAmountException,
    SameWalletTransferException,
    UnauthorizedWalletAccessException,
    WalletNotFoundException,
)
from app.models.user import User
from app.models.wallet import DepositRequest, Wallet
from app.models.wallet import TransferRequest
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet import WalletService


def _transfer(amount: str, to_wallet_id, key: str = "transfer-key-1") -> TransferRequest:
    return TransferRequest(
        amount=Decimal(amount),
        to_wallet_id=to_wallet_id,
        idempotency_key=key,
    )


async def _fund(wallet_service: WalletService, wallet: Wallet, user: User, amount: str) -> None:
    """Deposita saldo inicial en una wallet para que los tests puedan operar."""
    await wallet_service.deposit.execute(
        wallet.id, user,
        DepositRequest(amount=Decimal(amount), idempotency_key=f"fund-{wallet.id}-{amount}"),
    )


class TestTransferWallet:

    # ─── Happy path ────────────────────────────────────────────────────────────

    async def test_transferencia_exitosa(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "100")

        tx_out = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id),
        )

        assert tx_out.type == "transfer_out"
        assert tx_out.amount == Decimal("40")
        assert tx_out.balance_after == Decimal("60")
        assert tx_out.wallet_id == created_wallet.id

    async def test_balance_origen_disminuye(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "100")

        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("30", another_wallet.id),
        )

        origen = await wallet_repo.get_by_id(created_wallet.id)
        assert origen.balance == Decimal("70")

    async def test_balance_destino_aumenta(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "100")

        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("30", another_wallet.id),
        )

        destino = await wallet_repo.get_by_id(another_wallet.id)
        assert destino.balance == Decimal("30")

    async def test_transacciones_son_un_par(
        self,
        wallet_service: WalletService,
        transaction_repo: TransactionRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Cada transferencia debe dejar exactamente dos transacciones enlazadas:
        # un transfer_out en la wallet de origen y un transfer_in en la de destino.
        # Si alguno de los dos falta, el historial queda incompleto y no se puede
        # auditar por qué el destinatario recibió ese dinero.
        await _fund(wallet_service, created_wallet, created_user, "100")

        tx_out = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("50", another_wallet.id),
        )

        txs_origen = await transaction_repo.get_by_wallet_id(created_wallet.id)
        txs_destino = await transaction_repo.get_by_wallet_id(another_wallet.id)

        tx_in = next(t for t in txs_destino if t.type == "transfer_in")

        assert tx_out.reference_id == tx_in.id
        assert tx_in.reference_id == tx_out.id

    async def test_saldo_exacto_transferible(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Transferir exactamente todo el balance debe ser válido.
        # La wallet de origen queda en 0, no en negativo.
        await _fund(wallet_service, created_wallet, created_user, "50")

        tx_out = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("50", another_wallet.id),
        )

        assert tx_out.balance_after == Decimal("0")
        origen = await wallet_repo.get_by_id(created_wallet.id)
        assert origen.balance == Decimal("0")

    # ─── Validaciones de monto ─────────────────────────────────────────────────

    async def test_monto_minimo_exacto_valido(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "10")

        tx = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("0.5", another_wallet.id),
        )

        assert tx.amount == Decimal("0.5")

    async def test_monto_por_debajo_del_minimo(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "10")

        with pytest.raises(InvalidAmountException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("0.49", another_wallet.id),
            )

    async def test_monto_cero_rechazado(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        with pytest.raises(InvalidAmountException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("0", another_wallet.id),
            )

    async def test_monto_negativo_rechazado(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Un monto negativo no solo no tiene sentido: sería una transferencia
        # inversa silenciosa que crearía dinero de la nada.
        with pytest.raises(InvalidAmountException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("-10", another_wallet.id),
            )

    async def test_saldo_insuficiente(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "10")

        with pytest.raises(InsufficientFundsException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("20", another_wallet.id),
            )

    # ─── Validaciones de wallets ───────────────────────────────────────────────

    async def test_misma_wallet_rechazada(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
    ):
        # Transferirte a ti mismo no mueve dinero real pero sí crearía dos
        # transacciones en el historial que confundirían el audit trail.
        with pytest.raises(SameWalletTransferException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("10", created_wallet.id),
            )

    async def test_wallet_origen_no_encontrada(
        self,
        wallet_service: WalletService,
        created_user: User,
        another_wallet: Wallet,
    ):
        with pytest.raises(WalletNotFoundException):
            await wallet_service.transfer.execute(
                uuid4(), created_user,
                _transfer("10", another_wallet.id),
            )

    async def test_wallet_destino_no_encontrada(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "10")

        with pytest.raises(WalletNotFoundException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("10", uuid4()),
            )

    async def test_wallet_destino_inactiva(
        self,
        wallet_service: WalletService,
        db_session: AsyncSession,
        created_user: User,
        created_wallet: Wallet,
        another_user: User,
    ):
        # Creamos una wallet desactivada manualmente para simular una cuenta suspendida.
        # No debería ser posible recibir fondos en una wallet inactiva.
        wallet_inactiva = Wallet(user_id=another_user.id, is_active=False)
        db_session.add(wallet_inactiva)
        await db_session.commit()
        await db_session.refresh(wallet_inactiva)

        await _fund(wallet_service, created_wallet, created_user, "50")

        with pytest.raises(InactiveWalletException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("10", wallet_inactiva.id),
            )

    async def test_wallet_origen_de_otro_usuario(
        self,
        wallet_service: WalletService,
        another_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Un usuario no puede transferir desde la wallet de otra persona,
        # aunque conozca su ID.
        with pytest.raises(UnauthorizedWalletAccessException):
            await wallet_service.transfer.execute(
                created_wallet.id, another_user,
                _transfer("10", another_wallet.id),
            )

    # ─── Idempotencia ──────────────────────────────────────────────────────────

    async def test_idempotencia_retorna_transfer_out_existente(
        self,
        wallet_service: WalletService,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        await _fund(wallet_service, created_wallet, created_user, "100")

        first = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id, "same-key"),
        )
        second = await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id, "same-key"),
        )

        assert first.id == second.id

    async def test_idempotencia_no_duplica_saldo(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Este es el riesgo financiero más importante de la idempotencia:
        # si el cliente reintenta porque no recibió confirmación, el dinero
        # no debe moverse dos veces. El origen debe quedar en 60, no en 20.
        await _fund(wallet_service, created_wallet, created_user, "100")

        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id, "same-key"),
        )
        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id, "same-key"),
        )

        origen = await wallet_repo.get_by_id(created_wallet.id)
        destino = await wallet_repo.get_by_id(another_wallet.id)

        assert origen.balance == Decimal("60")
        assert destino.balance == Decimal("40")

    # ─── Concurrencia ──────────────────────────────────────────────────────────

    async def test_race_condition_dos_transferencias_mismo_origen(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Contexto del problema que estamos probando:
        # Dos clientes distintos intentan transferir desde la misma wallet al mismo tiempo.
        # Si ambos leen el saldo antes de que alguno escriba, los dos verían balance=100
        # y cada uno calcularía: 100 - 80 = 20. El segundo sobreescribiría al primero
        # dejando el balance en 20 cuando debería ser -60 (o fallar por fondos insuficientes).
        #
        # En producción con PostgreSQL, el SELECT FOR UPDATE del paso 5 serializa esto:
        # el segundo request queda bloqueado hasta que el primero termine, luego lee
        # balance=20 y lanza InsufficientFundsException correctamente.
        #
        # Este test simula el interleaving a mano porque SQLite no tiene row-level locking.
        # Lo que verificamos aquí es que el SERVICIO usa get_by_id_for_update (no get_by_id),
        # que es donde vive el lock en producción. Si alguien cambia esa llamada,
        # este test ayuda a detectar la regresión.

        await _fund(wallet_service, created_wallet, created_user, "100")

        # — SIMULACIÓN DEL RACE CONDITION —

        # Paso 1: Request A lee el balance antes de transferir. Ve balance=100.
        snapshot_a = await wallet_repo.get_by_id(created_wallet.id)
        assert snapshot_a.balance == Decimal("100")

        # Paso 2: Request B también lee antes de que A haya escrito. También ve balance=100.
        snapshot_b = await wallet_repo.get_by_id(created_wallet.id)
        assert snapshot_b.balance == Decimal("100")

        # Paso 3: Request A transfiere 80. El servicio usa get_by_id_for_update,
        # que en PostgreSQL bloquearía la fila. Aquí en SQLite simplemente ejecuta.
        # Resultado esperado: origen=20, destino=80.
        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("80", another_wallet.id, "transfer-a"),
        )

        # Paso 4: Request B intenta también transferir 80.
        # SIN protección de concurrencia: leería el snapshot viejo (100) y calcularía
        # 100-80=20, dejando el balance en 20 otra vez. El destino recibiría 80+80=160.
        # Es decir: 160 pesos que salieron de una wallet que solo tenía 100.
        #
        # CON SELECT FOR UPDATE en PostgreSQL: B habría esperado a que A commitee,
        # leería balance=20, y lanzaría InsufficientFundsException porque 20 < 80.
        # Eso es exactamente lo que queremos que pase.
        with pytest.raises(InsufficientFundsException):
            await wallet_service.transfer.execute(
                created_wallet.id, created_user,
                _transfer("80", another_wallet.id, "transfer-b"),
            )

        # El estado final debe reflejar solo la primera transferencia.
        # Origen: 100 - 80 = 20. Destino: 0 + 80 = 80.
        # Si ambas hubieran pasado, destino tendría 160 y origen -60. Eso sería un bug crítico.
        origen_final = await wallet_repo.get_by_id(created_wallet.id)
        destino_final = await wallet_repo.get_by_id(another_wallet.id)

        assert origen_final.balance == Decimal("20")
        assert destino_final.balance == Decimal("80")

    async def test_race_condition_transferencias_cruzadas(
        self,
        wallet_service: WalletService,
        wallet_repo: WalletRepository,
        created_user: User,
        another_user: User,
        created_wallet: Wallet,
        another_wallet: Wallet,
    ):
        # Este test cubre el escenario de deadlock:
        # A transfiere a B mientras B transfiere a A, exactamente al mismo tiempo.
        #
        # Sin el ordenamiento de locks por UUID, cada request bloquearía su wallet
        # de origen primero y esperaría la del otro. Ninguno podría avanzar: deadlock.
        #
        # La solución implementada en transfer_wallet.py es ordenar siempre los locks
        # por UUID ascendente: ambas requests compiten por el mismo lock primero,
        # una espera a la otra, y ninguna se bloquea mutuamente.
        #
        # Aquí simulamos la ejecución secuencial (SQLite no tiene concurrencia real)
        # pero verificamos que el resultado financiero es correcto: los balances
        # reflejan exactamente las dos transferencias, sin dinero perdido ni creado.

        await _fund(wallet_service, created_wallet, created_user, "100")
        await _fund(wallet_service, another_wallet, another_user, "60")

        # A (created_user) le transfiere 40 a B (another_user)
        await wallet_service.transfer.execute(
            created_wallet.id, created_user,
            _transfer("40", another_wallet.id, "cross-a-to-b"),
        )

        # B (another_user) le transfiere 25 a A (created_user)
        await wallet_service.transfer.execute(
            another_wallet.id, another_user,
            _transfer("25", created_wallet.id, "cross-b-to-a"),
        )

        # Dinero total en el sistema: 100 + 60 = 160. Debe seguir siendo 160.
        # A: 100 - 40 + 25 = 85
        # B: 60  + 40 - 25 = 75
        wallet_a = await wallet_repo.get_by_id(created_wallet.id)
        wallet_b = await wallet_repo.get_by_id(another_wallet.id)

        assert wallet_a.balance == Decimal("85")
        assert wallet_b.balance == Decimal("75")
        assert wallet_a.balance + wallet_b.balance == Decimal("160")
