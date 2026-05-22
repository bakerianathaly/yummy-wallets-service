from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationInfo(BaseModel):
    skip: int
    limit: int
    total_registros: int


class APIResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    outcome: list[T] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
