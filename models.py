"""
models.py
=========
Core domain classes for the banking application.

This module is the heart of the OOP demonstration. Every one of the
"4 pillars" of Object-Oriented Programming is deliberately and clearly
used here:

1. ENCAPSULATION
   - Sensitive state (`__balance`, `__pin_hash`) is stored as private
     attributes (double-underscore name mangling) and is only ever
     changed through controlled methods/properties that validate input.
   - Nobody outside the class can do `account.__balance = -999999`.

2. ABSTRACTION
   - `BankAccount` is an Abstract Base Class (ABC). It defines *what*
     every account must be able to do (deposit, withdraw, interest,
     account type, describe) without saying *how* each subtype does it.
   - Users of the class (e.g. the Streamlit UI, the `Bank` manager)
     only need to know the abstract interface, not the internal details.

3. INHERITANCE
   - `SavingsAccount`, `CurrentAccount`, and `FixedDepositAccount` all
     inherit the common fields/behaviour from `BankAccount` instead of
     re-implementing account number handling, transaction logging, etc.

4. POLYMORPHISM
   - The `Bank` class and the UI call `account.withdraw(amount)` or
     `account.calculate_interest()` on a *generic* `BankAccount`
     reference. The actual behaviour executed differs depending on the
     real (runtime) subclass -- that's polymorphism in action.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import itertools


# --------------------------------------------------------------------------
# Custom exceptions (clean error handling instead of silent failures)
# --------------------------------------------------------------------------
class InsufficientFundsError(Exception):
    """Raised when a withdrawal/transfer would break an account's rules."""


class InvalidAmountError(Exception):
    """Raised when an amount is zero, negative, or otherwise invalid."""


class AuthenticationError(Exception):
    """Raised when a PIN does not match an account."""


# --------------------------------------------------------------------------
# Supporting value object
# --------------------------------------------------------------------------
@dataclass
class Transaction:
    """A simple, immutable-by-convention record of one ledger event."""
    timestamp: str
    kind: str          # "DEPOSIT", "WITHDRAW", "TRANSFER_IN", "TRANSFER_OUT", "INTEREST"
    amount: float
    balance_after: float
    note: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @staticmethod
    def from_dict(d: dict) -> "Transaction":
        return Transaction(**d)


# --------------------------------------------------------------------------
# PILLAR 2: ABSTRACTION
# --------------------------------------------------------------------------
class BankAccount(ABC):
    """
    Abstract base class describing the contract every account type must
    fulfil. It cannot be instantiated directly -- try `BankAccount(...)`
    and Python will raise `TypeError` because of the `@abstractmethod`s.
    """

    _id_counter = itertools.count(1000)  # shared across all subclasses

    def __init__(self, owner_name: str, pin: str, opening_balance: float = 0.0):
        if opening_balance < 0:
            raise InvalidAmountError("Opening balance cannot be negative.")
        if not pin.isdigit() or len(pin) != 4:
            raise InvalidAmountError("PIN must be exactly 4 digits.")

        # ---------------- PILLAR 1: ENCAPSULATION ----------------
        # These attributes are name-mangled (prefixed with __) so they
        # cannot be accessed or overwritten directly from outside the
        # class, e.g. `acc.__balance = 1000000` will NOT work as intended.
        self.__account_number: int = next(BankAccount._id_counter)
        self.__owner_name: str = owner_name
        self.__balance: float = float(opening_balance)
        self.__pin_hash: str = self._hash_pin(pin)
        self.__transactions: list[Transaction] = []
        self.__created_at: str = datetime.now().isoformat(timespec="seconds")

        if opening_balance > 0:
            self._log_transaction("DEPOSIT", opening_balance, "Opening balance")

    # ---------------- helpers kept private to the class ----------------
    @staticmethod
    def _hash_pin(pin: str) -> str:
        # NOTE: this is a classroom/demo-grade hash (sha256, no salt).
        # It is NOT production-grade security -- a real bank would use
        # a proper salted password hashing scheme (e.g. bcrypt/argon2).
        return hashlib.sha256(pin.encode()).hexdigest()

    def _log_transaction(self, kind: str, amount: float, note: str = "") -> None:
        self.__transactions.append(
            Transaction(
                timestamp=datetime.now().isoformat(timespec="seconds"),
                kind=kind,
                amount=round(amount, 2),
                balance_after=round(self.__balance, 2),
                note=note,
            )
        )

    # ---------------- controlled read access (encapsulation) ----------------
    @property
    def account_number(self) -> int:
        return self.__account_number

    @property
    def owner_name(self) -> str:
        return self.__owner_name

    @property
    def balance(self) -> float:
        return round(self.__balance, 2)

    @property
    def created_at(self) -> str:
        return self.__created_at

    @property
    def transactions(self) -> list[Transaction]:
        # return a copy so callers can't mutate our private ledger
        return list(self.__transactions)

    def verify_pin(self, pin: str) -> bool:
        return self._hash_pin(pin) == self.__pin_hash

    def change_pin(self, old_pin: str, new_pin: str) -> None:
        if not self.verify_pin(old_pin):
            raise AuthenticationError("Old PIN is incorrect.")
        if not new_pin.isdigit() or len(new_pin) != 4:
            raise InvalidAmountError("New PIN must be exactly 4 digits.")
        self.__pin_hash = self._hash_pin(new_pin)

    # The only sanctioned way to change balance from inside this class
    # or its subclasses -- still private (name-mangled) to the outside.
    def _adjust_balance(self, delta: float) -> None:
        self.__balance = round(self.__balance + delta, 2)

    # ---------------- common behaviour, shared by all subclasses ----------------
    def deposit(self, amount: float, note: str = "") -> None:
        if amount <= 0:
            raise InvalidAmountError("Deposit amount must be positive.")
        self._adjust_balance(amount)
        self._log_transaction("DEPOSIT", amount, note)

    # ---------------- PILLAR 2: ABSTRACTION (abstract methods) ----------------
    @abstractmethod
    def withdraw(self, amount: float, note: str = "") -> None:
        """Each account type enforces its own withdrawal rules."""
        raise NotImplementedError

    @abstractmethod
    def calculate_interest(self) -> float:
        """Each account type has its own interest policy."""
        raise NotImplementedError

    @abstractmethod
    def account_type(self) -> str:
        """Human-readable account type name."""
        raise NotImplementedError

    # A concrete method that *uses* the abstract ones polymorphically
    def describe(self) -> str:
        return (
            f"[{self.account_type()}] #{self.account_number} "
            f"({self.owner_name}) — Balance: ₹{self.balance:,.2f}"
        )

    # ---------------- serialization (for JSON persistence) ----------------
    def to_dict(self) -> dict:
        base = {
            "class": self.__class__.__name__,
            "account_number": self.__account_number,
            "owner_name": self.__owner_name,
            "balance": self.__balance,
            "pin_hash": self.__pin_hash,
            "created_at": self.__created_at,
            "transactions": [t.to_dict() for t in self.__transactions],
        }
        base.update(self._extra_fields())
        return base

    def _extra_fields(self) -> dict:
        """Subclasses override to persist their extra attributes."""
        return {}

    def _restore_common(self, d: dict) -> None:
        self.__account_number = d["account_number"]
        self.__owner_name = d["owner_name"]
        self.__balance = d["balance"]
        self.__pin_hash = d["pin_hash"]
        self.__created_at = d["created_at"]
        self.__transactions = [Transaction.from_dict(t) for t in d["transactions"]]


# --------------------------------------------------------------------------
# PILLAR 3: INHERITANCE  +  PILLAR 4: POLYMORPHISM
# --------------------------------------------------------------------------
class SavingsAccount(BankAccount):
    """Earns interest; enforces a minimum balance on withdrawal."""

    MIN_BALANCE = 500.0
    INTEREST_RATE = 0.04  # 4% per "interest cycle" (demo purposes)

    def withdraw(self, amount: float, note: str = "") -> None:
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive.")
        if self.balance - amount < self.MIN_BALANCE:
            raise InsufficientFundsError(
                f"Savings accounts must keep a minimum balance of "
                f"₹{self.MIN_BALANCE:,.2f}."
            )
        self._adjust_balance(-amount)
        self._log_transaction("WITHDRAW", amount, note)

    def calculate_interest(self) -> float:
        return round(self.balance * self.INTEREST_RATE, 2)

    def account_type(self) -> str:
        return "Savings Account"

    @classmethod
    def restore(cls, d: dict) -> "SavingsAccount":
        obj = cls.__new__(cls)
        obj._restore_common(d)
        return obj


class CurrentAccount(BankAccount):
    """Business/checking-style account: no interest, has an overdraft limit."""

    OVERDRAFT_LIMIT = 10000.0

    def withdraw(self, amount: float, note: str = "") -> None:
        if amount <= 0:
            raise InvalidAmountError("Withdrawal amount must be positive.")
        if self.balance - amount < -self.OVERDRAFT_LIMIT:
            raise InsufficientFundsError(
                f"Withdrawal exceeds overdraft limit of ₹{self.OVERDRAFT_LIMIT:,.2f}."
            )
        self._adjust_balance(-amount)
        self._log_transaction("WITHDRAW", amount, note)

    def calculate_interest(self) -> float:
        return 0.0  # current accounts earn no interest

    def account_type(self) -> str:
        return "Current Account"

    @classmethod
    def restore(cls, d: dict) -> "CurrentAccount":
        obj = cls.__new__(cls)
        obj._restore_common(d)
        return obj


class FixedDepositAccount(BankAccount):
    """Locked-in deposit: withdrawals are blocked, higher interest rate."""

    INTEREST_RATE = 0.07  # 7% per cycle (demo purposes)

    def withdraw(self, amount: float, note: str = "") -> None:
        raise InsufficientFundsError(
            "Fixed Deposit accounts do not allow withdrawals until maturity."
        )

    def calculate_interest(self) -> float:
        return round(self.balance * self.INTEREST_RATE, 2)

    def account_type(self) -> str:
        return "Fixed Deposit Account"

    @classmethod
    def restore(cls, d: dict) -> "FixedDepositAccount":
        obj = cls.__new__(cls)
        obj._restore_common(d)
        return obj


# Map used by the persistence layer to rebuild the right subclass
ACCOUNT_CLASSES = {
    "SavingsAccount": SavingsAccount,
    "CurrentAccount": CurrentAccount,
    "FixedDepositAccount": FixedDepositAccount,
}
