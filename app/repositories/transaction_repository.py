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

    async def get_by_wallet_id(self, wallet_id: UUID) -> list[Transaction]:
        result = await self.db.execute(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .order_by(Transaction.created_at.desc())
        )
        return list(result.scalars().all())
