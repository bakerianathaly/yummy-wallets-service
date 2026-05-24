from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository
from app.services.wallet.create_wallet import CreateWallet
from app.services.wallet.deposit_wallet import DepositWallet
from app.services.wallet.get_wallet_summary import GetWalletSummary
from app.services.wallet.get_wallet_transactions import GetWalletTransactions
from app.services.wallet.transfer_wallet import TransferWallet
from app.services.wallet.withdraw_wallet import WithdrawWallet


class WalletService:
    def __init__(
        self, wallet_repo: WalletRepository, transaction_repo: TransactionRepository
    ):
        self.create = CreateWallet(wallet_repo)
        self.deposit = DepositWallet(wallet_repo, transaction_repo)
        self.withdraw = WithdrawWallet(wallet_repo, transaction_repo)
        self.transfer = TransferWallet(wallet_repo, transaction_repo)
        self.get_summary = GetWalletSummary(wallet_repo, transaction_repo)
        self.get_transactions = GetWalletTransactions(wallet_repo, transaction_repo)
