"""
bank.py
=======
`Bank` is the manager/service class that sits on top of the domain
model (`models.py`). It demonstrates **polymorphism** very directly:
every method here (deposit, withdraw, interest run) operates on
`BankAccount` references without caring which concrete subclass
(`SavingsAccount`, `CurrentAccount`, `FixedDepositAccount`) is actually
behind that reference.

It also owns persistence: accounts are saved to / loaded from a JSON
file on disk so data survives app restarts (no external database
needed for this demo).
"""

from __future__ import annotations

import json
import os
from typing import Optional

from models import (
    BankAccount,
    SavingsAccount,
    CurrentAccount,
    FixedDepositAccount,
    ACCOUNT_CLASSES,
    InsufficientFundsError,
    InvalidAmountError,
    AuthenticationError,
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "bank_data.json")


class Bank:
    def __init__(self, name: str = "PyBank"):
        self.name = name
        self._accounts: dict[int, BankAccount] = {}
        self.load()

    # ---------------------------------------------------------------
    # Account creation (factory-style method, hides which subclass
    # gets instantiated based on a simple string the UI passes in --
    # this is a common companion pattern to polymorphism)
    # ---------------------------------------------------------------
    def open_account(
        self, owner_name: str, pin: str, account_type: str, opening_balance: float = 0.0
    ) -> BankAccount:
        owner_name = owner_name.strip()
        if not owner_name:
            raise InvalidAmountError("Owner name cannot be empty.")

        if account_type == "Savings":
            account: BankAccount = SavingsAccount(owner_name, pin, opening_balance)
        elif account_type == "Current":
            account = CurrentAccount(owner_name, pin, opening_balance)
        elif account_type == "Fixed Deposit":
            account = FixedDepositAccount(owner_name, pin, opening_balance)
        else:
            raise ValueError(f"Unknown account type: {account_type}")

        self._accounts[account.account_number] = account
        self.save()
        return account

    # ---------------------------------------------------------------
    # Lookup / auth
    # ---------------------------------------------------------------
    def get_account(self, account_number: int) -> Optional[BankAccount]:
        return self._accounts.get(int(account_number))

    def authenticate(self, account_number: int, pin: str) -> BankAccount:
        account = self.get_account(account_number)
        if account is None:
            raise AuthenticationError("No account with that number exists.")
        if not account.verify_pin(pin):
            raise AuthenticationError("Incorrect PIN.")
        return account

    def all_accounts(self) -> list[BankAccount]:
        return sorted(self._accounts.values(), key=lambda a: a.account_number)

    # ---------------------------------------------------------------
    # Core operations -- all POLYMORPHIC: `account` below is typed as
    # BankAccount, but .withdraw()/.calculate_interest() run whichever
    # overridden version belongs to the real subclass at runtime.
    # ---------------------------------------------------------------
    def deposit(self, account_number: int, amount: float, note: str = "") -> BankAccount:
        account = self._require_account(account_number)
        account.deposit(amount, note)
        self.save()
        return account

    def withdraw(self, account_number: int, amount: float, note: str = "") -> BankAccount:
        account = self._require_account(account_number)
        account.withdraw(amount, note)  # <-- polymorphic dispatch
        self.save()
        return account

    def transfer(
        self, from_account_number: int, to_account_number: int, amount: float, note: str = ""
    ) -> tuple[BankAccount, BankAccount]:
        if from_account_number == to_account_number:
            raise InvalidAmountError("Cannot transfer to the same account.")
        src = self._require_account(from_account_number)
        dst = self._require_account(to_account_number)

        src.withdraw(amount, note or f"Transfer to #{to_account_number}")
        try:
            dst.deposit(amount, note or f"Transfer from #{from_account_number}")
        except InvalidAmountError:
            # roll back the withdrawal if the deposit side fails validation
            src.deposit(amount, "Reversal of failed transfer")
            raise

        self.save()
        return src, dst

    def run_interest_cycle(self) -> dict[int, float]:
        """
        Apply one interest cycle to every account that earns interest.
        Demonstrates polymorphism across a heterogeneous collection:
        the *same* loop/method call produces different results (incl.
        zero for CurrentAccount) depending on each object's real class.
        """
        applied = {}
        for account in self._accounts.values():
            interest = account.calculate_interest()
            if interest > 0:
                account.deposit(interest, "Interest credited")
                applied[account.account_number] = interest
        self.save()
        return applied

    def _require_account(self, account_number: int) -> BankAccount:
        account = self.get_account(account_number)
        if account is None:
            raise ValueError(f"Account #{account_number} does not exist.")
        return account

    # ---------------------------------------------------------------
    # Persistence
    # ---------------------------------------------------------------
    def save(self) -> None:
        data = {
            "bank_name": self.name,
            "accounts": [acc.to_dict() for acc in self._accounts.values()],
        }
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def load(self) -> None:
        if not os.path.exists(DATA_FILE):
            return
        try:
            with open(DATA_FILE) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        self.name = data.get("bank_name", self.name)
        self._accounts = {}
        for raw in data.get("accounts", []):
            cls = ACCOUNT_CLASSES.get(raw["class"])
            if cls is None:
                continue
            account = cls.restore(raw)
            self._accounts[account.account_number] = account

        # keep the id counter ahead of every restored account so new
        # accounts never collide with restored ones
        if self._accounts:
            import itertools
            from models import BankAccount as _BA
            max_id = max(self._accounts.keys())
            _BA._id_counter = itertools.count(max_id + 1)

    def reset(self) -> None:
        """Wipe all data -- used by the 'reset demo data' button."""
        self._accounts = {}
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
