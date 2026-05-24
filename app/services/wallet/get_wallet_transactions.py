import math

from app.exceptions import WalletNotFoundException
from app.models.user import User
from app.models.wallet import PaginatedTransactionsResponse, TransactionResponse
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20


class GetWalletTransactions:
    def __init__(self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository):
        self.wallet_repo = wallet_repo
        self.transaction_repo = transaction_repo

    async def execute(self, user: User, page: int, page_size: int) -> PaginatedTransactionsResponse:
        page = max(1, page)
        page_size = max(1, min(page_size, MAX_PAGE_SIZE))

        wallet = await self.wallet_repo.get_by_user_id(user.id)
        if wallet is None:
            raise WalletNotFoundException("El usuario no tiene una wallet")

        transactions, total = await self.transaction_repo.get_paginated_by_wallet_id(
            wallet.id, page, page_size
        )
        total_pages = math.ceil(total / page_size) if total > 0 else 1

        return PaginatedTransactionsResponse(
            transactions=[TransactionResponse.model_validate(tx) for tx in transactions],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
