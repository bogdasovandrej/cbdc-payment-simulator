"""Сервис пользовательских данных: баланс и история операций."""
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.transaction import Transaction
from app.models.user import User
from app.models.wallet import Wallet
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.wallet_repository import WalletRepository


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.wallets = WalletRepository(db)
        self.transactions = TransactionRepository(db)

    def get_wallet(self, user: User) -> Wallet:
        wallet = self.wallets.get_by_user_id(user.id)
        if wallet is None:
            raise NotFoundError("Кошелёк не найден")
        return wallet

    def get_transactions(self, user: User) -> list[Transaction]:
        wallet = self.get_wallet(user)
        return self.transactions.list_by_wallet(wallet.id)
