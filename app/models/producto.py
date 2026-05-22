import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlmodel import Field, SQLModel


# ─── Modelo DB ───────────────────────────────────────────────
class Producto(SQLModel, table=True):
    __tablename__ = "products"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(UUID, primary_key=True),
    )
    nombre: str = Field(max_length=255)
    descripcion: Optional[str] = Field(default=None, sa_column=Column(Text))
    precio: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.now
    )
    updated_at: datetime = Field(
            default_factory=datetime.now,
            sa_column_kwargs={
                "server_default": func.now(),
                "onupdate": func.now(),
            },
            nullable=False,
        )


# ─── Schemas API ─────────────────────────────────────────────
class ProductoCreate(SQLModel):
    nombre: str = Field(max_length=255)  # Se puede usar min_length=1
    descripcion: Optional[str] = None
    precio: Decimal = Field(decimal_places=2)  # Se puede usar gt=0
    stock: int = Field(default=0)  # Se puede usar ge=0


class ProductoUpdate(SQLModel):
    nombre: Optional[str] = Field(default=None, max_length=255)
    descripcion: Optional[str] = None
    precio: Optional[Decimal] = Field(default=None, decimal_places=2)
    stock: Optional[int] = None


class ProductoResponse(SQLModel):
    id: uuid.UUID
    nombre: str
    descripcion: Optional[str]
    precio: Decimal
    stock: int
    created_at: datetime
    updated_at: Optional[datetime]
