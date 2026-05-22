from app.repositories.wallet_repository import WalletRepository
from app.services.wallet.create_wallet import CreateWallet


class WalletService:
    def __init__(self, repository: WalletRepository):
        self.create = CreateWallet(repository)
