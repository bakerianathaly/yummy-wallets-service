from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet.create_wallet import CreateWallet
from app.services.wallet.deposit_wallet import DepositWallet


class WalletService:
    def __init__(self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository):
        self.create = CreateWallet(wallet_repo)
        self.deposit = DepositWallet(wallet_repo, transaction_repo)
