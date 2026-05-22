from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet


class WalletRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, wallet: Wallet) -> Wallet:
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def get_by_id(self, wallet_id: UUID) -> Optional[Wallet]:
        return await self.db.get(Wallet, wallet_id)

    async def get_by_user_id(self, user_id: UUID) -> Optional[Wallet]:
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()
