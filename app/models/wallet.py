import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel

# ─── Modelos DB ───────────────────────────────────────────────


class Wallet(SQLModel, table=True):
    __tablename__ = "wallets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", unique=True, index=True)
    balance: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=6)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(foreign_key="wallets.id", index=True)
    type: str = Field(
        max_length=20
    )  # deposit | withdrawal | transfer_in | transfer_out
    amount: Decimal = Field(max_digits=18, decimal_places=6)
    balance_after: Decimal = Field(max_digits=18, decimal_places=6)
    reference_id: Optional[uuid.UUID] = Field(default=None, index=True)
    idempotency_key: Optional[str] = Field(default=None, max_length=255, unique=True)
    description: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=datetime.now)


# ─── Schemas API ──────────────────────────────────────────────


class WalletResponse(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TransactionResponse(SQLModel):
    id: uuid.UUID
    wallet_id: uuid.UUID
    type: str
    amount: Decimal
    balance_after: Decimal
    reference_id: Optional[uuid.UUID]
    description: Optional[str]
    created_at: datetime


class DepositRequest(SQLModel):
    amount: Decimal
    idempotency_key: str
    description: Optional[str] = None


class WithdrawalRequest(SQLModel):
    amount: Decimal
    idempotency_key: str
    description: Optional[str] = None


class TransferRequest(SQLModel):
    to_wallet_id: uuid.UUID
    amount: Decimal
    idempotency_key: str
    description: Optional[str] = None
