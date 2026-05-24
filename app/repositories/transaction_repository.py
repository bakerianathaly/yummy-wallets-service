from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DatabaseException
from app.models.wallet import Transaction


class TransactionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, transaction: Transaction) -> Transaction:
        try:
            self.db.add(transaction)
            await self.db.commit()
            await self.db.refresh(transaction)
            return transaction
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException("Error al crear la transacción") from e

    async def get_by_idempotency_key(self, key: str) -> Optional[Transaction]:
        result = await self.db.execute(
            select(Transaction).where(Transaction.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def save_transfer_pair(
        self, tx_out: Transaction, tx_in: Transaction
    ) -> tuple[Transaction, Transaction]:
        try:
            # Agregamos los dos lados al mismo tiempo sin commitear todavía.
            # Necesitamos que la DB les asigne IDs antes de poder cruzar las referencias.
            self.db.add(tx_out)
            self.db.add(tx_in)
            await self.db.flush()
            await self.db.refresh(tx_out)
            await self.db.refresh(tx_in)

            # Ahora que tenemos los IDs, cada transacción apunta a su contraparte.
            # Esto es lo que permite reconstruir el par completo desde cualquier lado.
            tx_out.reference_id = tx_in.id
            tx_in.reference_id = tx_out.id
            self.db.add(tx_out)
            self.db.add(tx_in)
            await self.db.flush()

            # Un solo commit cierra todo: ambas actualizaciones de balance (que
            # ya venían como flush desde el servicio) + ambas transacciones + sus referencias.
            await self.db.commit()
            await self.db.refresh(tx_out)
            await self.db.refresh(tx_in)
            return tx_out, tx_in
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException("Error al crear las transacciones de transferencia") from e

    async def get_by_wallet_id(self, wallet_id: UUID) -> list[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())
