from app.exceptions import WalletNotFoundException
from app.models.user import User
from app.models.wallet import TransactionResponse, WalletSummaryResponse
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository

RECENT_LIMIT = 10


class GetWalletSummary:
    def __init__(
        self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository
    ):
        self.wallet_repo = wallet_repo
        self.transaction_repo = transaction_repo

    async def execute(self, user: User) -> WalletSummaryResponse:
        wallet = await self.wallet_repo.get_by_user_id(user.id)
        if wallet is None:
            raise WalletNotFoundException("El usuario no tiene una wallet")

        recent = await self.transaction_repo.get_recent_by_wallet_id(
            wallet.id, limit=RECENT_LIMIT
        )

        return WalletSummaryResponse(
            id=wallet.id,
            balance=wallet.balance,
            is_active=wallet.is_active,
            created_at=wallet.created_at,
            recent_transactions=[
                TransactionResponse.model_validate(tx) for tx in recent
            ],
        )
