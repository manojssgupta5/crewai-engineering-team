import uuid
from typing import Dict, List
from dataclasses import dataclass


class InsufficientFundsError(Exception):
    """Raised when attempting to withdraw or buy shares with insufficient funds."""
    pass


class InsufficientSharesError(Exception):
    """Raised when attempting to sell shares without sufficient holdings."""
    pass


class InvalidSymbolError(Exception):
    """Raised when attempting to operate on an invalid ticker symbol."""
    pass


class AccountManager:
    """
    Encapsulates the logic for managing a single trading account.
    """

    VALID_SYMBOLS = ["AAPL", "TSLA", "GOOGL"]

    def __init__(self, initial_deposit: float) -> None:
        """
        Initializes a new AccountManager instance.

        Args:
            initial_deposit: The initial deposit amount.

        Raises:
            ValueError: if initial_deposit is not positive.
        """
        if not initial_deposit > 0:
            raise ValueError("Initial deposit must be positive.")

        self.account_id = str(uuid.uuid4())
        self.cash = initial_deposit
        self.holdings: Dict[str, int] = {}
        self.transaction_history: List[Dict] = []
        self.initial_deposit = initial_deposit

    def deposit(self, amount: float) -> None:
        """
        Deposits funds into the account.

        Args:
            amount: The amount to deposit.

        Raises:
            ValueError: if amount is not positive.
        """
        if not amount > 0:
            raise ValueError("Deposit amount must be positive.")

        self.cash += amount
        self.transaction_history.append(
            {
                "type": "deposit",
                "symbol": None,
                "quantity": None,
                "price": None,
                "timestamp": None,
            }
        )

    def withdraw(self, amount: float) -> None:
        """
        Withdraws funds from the account.

        Args:
            amount: The amount to withdraw.

        Raises:
            ValueError: if amount is not positive.
            InsufficientFundsError: if withdrawing amount would result in a negative cash balance.
        """
        if not amount > 0:
            raise ValueError("Withdrawal amount must be positive.")

        if self.cash < amount:
            raise InsufficientFundsError("Insufficient funds.")

        self.cash -= amount
        self.transaction_history.append(
            {
                "type": "withdrawal",
                "symbol": None,
                "quantity": None,
                "price": None,
                "timestamp": None,
            }
        )

    def buy_shares(self, symbol: str, quantity: int) -> None:
        """
        Purchases shares of a given symbol.

        Args:
            symbol: The ticker symbol of the shares to purchase.
            quantity: The number of shares to purchase.

        Raises:
            ValueError: if symbol is invalid or quantity is not positive.
            InsufficientFundsError: if the purchase cannot be completed due to insufficient cash.
        """
        if symbol not in self.VALID_SYMBOLS:
            raise ValueError(f"Invalid symbol: {symbol}. Valid symbols are {self.VALID_SYMBOLS}")

        if not quantity > 0:
            raise ValueError("Quantity must be positive.")

        price = self.get_share_price(symbol)
        cost = price * quantity

        if self.cash < cost:
            raise InsufficientFundsError("Insufficient funds.")

        self.cash -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + quantity
        self.transaction_history.append(
            {
                "type": "buy",
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "timestamp": None,
            }
        )

    def sell_shares(self, symbol: str, quantity: int) -> None:
        """
        Sells shares of a given symbol.

        Args:
            symbol: The ticker symbol of the shares to sell.
            quantity: The number of shares to sell.

        Raises:
            ValueError: if symbol is invalid or quantity is not positive.
            InsufficientSharesError: if the sale cannot be completed due to insufficient holdings.
        """
        if symbol not in self.VALID_SYMBOLS:
            raise ValueError(f"Invalid symbol: {symbol}. Valid symbols are {self.VALID_SYMBOLS}")

        if not quantity > 0:
            raise ValueError("Quantity must be positive.")

        if symbol not in self.holdings or self.holdings[symbol] < quantity:
            raise InsufficientSharesError("Insufficient shares.")

        price = self.get_share_price(symbol)
        self.holdings[symbol] -= quantity
        self.cash += price * quantity
        self.transaction_history.append(
            {
                "type": "sell",
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "timestamp": None,
            }
        )

    def get_account_status(self) -> Dict:
        """
        Returns a dictionary containing the account status.

        Returns:
            dict: A dictionary containing cash, holdings, transaction_history, portfolio_value, and profit_loss.
        """
        portfolio_value = self.cash
        for symbol, quantity in self.holdings.items():
            portfolio_value += quantity * self.get_share_price(symbol)

        profit_loss = portfolio_value - self.initial_deposit

        return {
            "cash": self.cash,
            "holdings": self.holdings,
            "transaction_history": self.transaction_history,
            "portfolio_value": portfolio_value,
            "profit_loss": profit_loss,
        }

    def get_share_price(self, symbol: str) -> float:
        """
        Returns the current price of a share.

        Args:
            symbol: The ticker symbol of the share.

        Returns:
            float: The share price.

        Raises:
            ValueError: If symbol is not supported.
        """
        if symbol == "AAPL":
            return 170.34
        elif symbol == "TSLA":
            return 250.56
        elif symbol == "GOOGL":
            return 2700.42
        else:
            raise ValueError(f"Unsupported symbol: {symbol}")
