from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import CompileError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import DatabaseException
from app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, wallet: Wallet) -> Wallet:
        try:
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)
            return wallet
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException("Error al crear la wallet") from e

    async def get_by_id(self, wallet_id: UUID) -> Optional[Wallet]:
        return await self.db.get(Wallet, wallet_id)

    async def get_by_id_for_update(self, wallet_id: UUID) -> Optional[Wallet]:
        # WITH FOR UPDATE serializa escrituras concurrentes en PostgreSQL.
        # SQLite (usado en tests) no lo soporta; se cae al read normal.
        try:
            result = await self.db.execute(
                select(Wallet).where(Wallet.id == wallet_id).with_for_update()
            )
        except CompileError:
            result = await self.db.execute(
                select(Wallet).where(Wallet.id == wallet_id)
            )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Wallet]:
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_balance(self, wallet: Wallet, new_balance: Decimal) -> Wallet:
        try:
            wallet.balance = new_balance
            wallet.updated_at = datetime.now()
            self.db.add(wallet)
            await self.db.flush()
            await self.db.refresh(wallet)
            return wallet
        except Exception as e:
            await self.db.rollback()
            raise DatabaseException("Error al actualizar el balance de la wallet") from e
