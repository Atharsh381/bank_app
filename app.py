"""
app.py
======
Streamlit front-end for the OOP Banking demo.

Run with:   streamlit run app.py

This file is intentionally "thin" -- it contains no business rules.
All banking logic lives in `models.py` (domain/OOP pillars) and
`bank.py` (manager + persistence). The UI only calls into those layers
and renders the result, which is good separation of concerns.
"""

import streamlit as st
import pandas as pd

from bank import Bank
from models import InsufficientFundsError, InvalidAmountError, AuthenticationError

st.set_page_config(page_title="PyBank — OOP Banking Demo", page_icon="🏦", layout="wide")

# ---------------------------------------------------------------------------
# Session state setup
# ---------------------------------------------------------------------------
if "bank" not in st.session_state:
    st.session_state.bank = Bank("PyBank")
if "logged_in_account" not in st.session_state:
    st.session_state.logged_in_account = None  # holds an account_number (int)

bank: Bank = st.session_state.bank


def logged_in_account():
    if st.session_state.logged_in_account is None:
        return None
    return bank.get_account(st.session_state.logged_in_account)


# ---------------------------------------------------------------------------
# Sidebar: branding + login/logout + quick nav
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🏦 PyBank")
    st.caption("A Streamlit banking demo built on 4 OOP pillars")

    acc = logged_in_account()
    if acc:
        st.success(f"Logged in as\n\n**{acc.owner_name}**\n\nAcc #{acc.account_number}")
        if st.button("Log out", use_container_width=True):
            st.session_state.logged_in_account = None
            st.rerun()
    else:
        st.info("Not logged in. Open an account or log in below.")

    st.divider()
    with st.expander("⚠️ Demo data controls"):
        st.caption("Resets ALL accounts and transaction history.")
        if st.button("Reset all demo data", type="secondary"):
            bank.reset()
            st.session_state.logged_in_account = None
            st.success("All data cleared.")
            st.rerun()

st.title("Banking Application")

tabs = st.tabs(
    [
        "🔐 Login",
        "➕ Open Account",
        "💰 Deposit",
        "💸 Withdraw",
        "🔁 Transfer",
        "📜 Statement",
        "📈 Interest",
        "🗂️ All Accounts (Admin)",
        "🧠 OOP Explainer",
    ]
)

# ---------------------------------------------------------------------------
# TAB: Login
# ---------------------------------------------------------------------------
with tabs[0]:
    st.subheader("Log in to an existing account")
    with st.form("login_form"):
        acc_num = st.number_input("Account number", min_value=0, step=1, value=0)
        pin = st.text_input("4-digit PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Log in")

    if submitted:
        try:
            account = bank.authenticate(int(acc_num), pin)
            st.session_state.logged_in_account = account.account_number
            st.success(f"Welcome back, {account.owner_name}!")
            st.rerun()
        except AuthenticationError as e:
            st.error(str(e))

# ---------------------------------------------------------------------------
# TAB: Open Account
# ---------------------------------------------------------------------------
with tabs[1]:
    st.subheader("Open a new account")
    st.caption(
        "Choose an account type. Each type is a different **subclass** of the "
        "abstract `BankAccount` class, with its own withdrawal rules and "
        "interest policy (inheritance + polymorphism)."
    )
    with st.form("open_account_form"):
        name = st.text_input("Full name")
        acc_type = st.selectbox("Account type", ["Savings", "Current", "Fixed Deposit"])
        new_pin = st.text_input("Set a 4-digit PIN", type="password", max_chars=4)
        opening_balance = st.number_input("Opening balance (₹)", min_value=0.0, step=100.0)

        col_info = {
            "Savings": "Earns 4% interest per cycle. Minimum balance ₹500 enforced.",
            "Current": "No interest. Overdraft up to ₹10,000 allowed.",
            "Fixed Deposit": "Earns 7% interest per cycle. Withdrawals are locked.",
        }
        st.info(col_info[acc_type])

        submitted = st.form_submit_button("Open account")

    if submitted:
        try:
            account = bank.open_account(name, new_pin, acc_type, opening_balance)
            st.success(
                f"Account created! Your account number is **#{account.account_number}** "
                f"— save this to log in."
            )
            st.balloons()
        except (InvalidAmountError, ValueError) as e:
            st.error(str(e))

# ---------------------------------------------------------------------------
# TAB: Deposit
# ---------------------------------------------------------------------------
with tabs[2]:
    st.subheader("Deposit funds")
    account = logged_in_account()
    if not account:
        st.warning("Please log in first (see the Login tab).")
    else:
        st.metric("Current balance", f"₹{account.balance:,.2f}")
        with st.form("deposit_form"):
            amount = st.number_input("Amount to deposit (₹)", min_value=0.0, step=100.0)
            note = st.text_input("Note (optional)")
            submitted = st.form_submit_button("Deposit")
        if submitted:
            try:
                bank.deposit(account.account_number, amount, note)
                st.success(f"Deposited ₹{amount:,.2f}. New balance: ₹{logged_in_account().balance:,.2f}")
                st.rerun()
            except InvalidAmountError as e:
                st.error(str(e))

# ---------------------------------------------------------------------------
# TAB: Withdraw
# ---------------------------------------------------------------------------
with tabs[3]:
    st.subheader("Withdraw funds")
    account = logged_in_account()
    if not account:
        st.warning("Please log in first (see the Login tab).")
    else:
        st.metric("Current balance", f"₹{account.balance:,.2f}")
        st.caption(f"Account type: **{account.account_type()}**")
        with st.form("withdraw_form"):
            amount = st.number_input("Amount to withdraw (₹)", min_value=0.0, step=100.0)
            note = st.text_input("Note (optional)")
            submitted = st.form_submit_button("Withdraw")
        if submitted:
            try:
                bank.withdraw(account.account_number, amount, note)
                st.success(f"Withdrew ₹{amount:,.2f}. New balance: ₹{logged_in_account().balance:,.2f}")
                st.rerun()
            except (InsufficientFundsError, InvalidAmountError) as e:
                st.error(str(e))

# ---------------------------------------------------------------------------
# TAB: Transfer
# ---------------------------------------------------------------------------
with tabs[4]:
    st.subheader("Transfer to another account")
    account = logged_in_account()
    if not account:
        st.warning("Please log in first (see the Login tab).")
    else:
        st.metric("Current balance", f"₹{account.balance:,.2f}")
        with st.form("transfer_form"):
            to_acc = st.number_input("Recipient account number", min_value=0, step=1)
            amount = st.number_input("Amount to transfer (₹)", min_value=0.0, step=100.0)
            note = st.text_input("Note (optional)")
            submitted = st.form_submit_button("Transfer")
        if submitted:
            try:
                src, dst = bank.transfer(account.account_number, int(to_acc), amount, note)
                st.success(
                    f"Transferred ₹{amount:,.2f} to #{dst.account_number} ({dst.owner_name}). "
                    f"Your new balance: ₹{src.balance:,.2f}"
                )
                st.rerun()
            except (InsufficientFundsError, InvalidAmountError, ValueError) as e:
                st.error(str(e))

# ---------------------------------------------------------------------------
# TAB: Statement
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Transaction history")
    account = logged_in_account()
    if not account:
        st.warning("Please log in first (see the Login tab).")
    else:
        st.write(account.describe())
        txns = account.transactions
        if not txns:
            st.info("No transactions yet.")
        else:
            df = pd.DataFrame([t.to_dict() for t in reversed(txns)])
            df = df.rename(
                columns={
                    "timestamp": "When",
                    "kind": "Type",
                    "amount": "Amount (₹)",
                    "balance_after": "Balance After (₹)",
                    "note": "Note",
                }
            )
            st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# TAB: Interest
# ---------------------------------------------------------------------------
with tabs[6]:
    st.subheader("Interest engine (polymorphism in action)")
    st.caption(
        "Clicking the button below calls `account.calculate_interest()` on "
        "**every account in the bank**, regardless of type. Savings and Fixed "
        "Deposit accounts credit interest; Current accounts correctly get ₹0 "
        "— the *same* method call, different behaviour per subclass."
    )
    if st.button("Run interest cycle for all accounts"):
        applied = bank.run_interest_cycle()
        if not applied:
            st.info("No accounts currently earn interest (or no accounts exist yet).")
        else:
            rows = [
                {
                    "Account": f"#{num} — {bank.get_account(num).owner_name}",
                    "Type": bank.get_account(num).account_type(),
                    "Interest Credited (₹)": amt,
                }
                for num, amt in applied.items()
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.success(f"Interest applied to {len(applied)} account(s).")

# ---------------------------------------------------------------------------
# TAB: Admin / all accounts
# ---------------------------------------------------------------------------
with tabs[7]:
    st.subheader("All accounts in the bank")
    accounts = bank.all_accounts()
    if not accounts:
        st.info("No accounts yet — open one in the 'Open Account' tab.")
    else:
        rows = [
            {
                "Account #": a.account_number,
                "Owner": a.owner_name,
                "Type": a.account_type(),
                "Balance (₹)": a.balance,
                "Opened": a.created_at,
            }
            for a in accounts
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(f"Total accounts: {len(accounts)}  •  Total holdings: ₹{sum(a.balance for a in accounts):,.2f}")

# ---------------------------------------------------------------------------
# TAB: OOP Explainer
# ---------------------------------------------------------------------------
with tabs[8]:
    st.subheader("Where are the 4 pillars of OOP in this code?")
    st.markdown(
        """
| Pillar | Where it lives | What to look at |
|---|---|---|
| **Encapsulation** | `models.py` → `BankAccount.__init__` | `__balance`, `__pin_hash`, `__transactions` are private (name-mangled). They can only be changed via validated methods like `deposit()`, `withdraw()`, `change_pin()` — never set directly from outside. |
| **Abstraction** | `models.py` → `class BankAccount(ABC)` | `withdraw()`, `calculate_interest()`, `account_type()` are declared `@abstractmethod`. You cannot even create a bare `BankAccount()` — Python enforces that every real account type must supply its own implementation. |
| **Inheritance** | `models.py` → `SavingsAccount`, `CurrentAccount`, `FixedDepositAccount` | Each class inherits shared fields/methods (`deposit`, `balance`, transaction logging, PIN handling) from `BankAccount` instead of duplicating that code. |
| **Polymorphism** | `bank.py` → `Bank.withdraw()`, `Bank.run_interest_cycle()` | These methods call `account.withdraw(...)` / `account.calculate_interest()` on a variable typed only as `BankAccount`. At runtime, Python dispatches to the correct overridden version depending on whether the object is actually a `SavingsAccount`, `CurrentAccount`, or `FixedDepositAccount`. |
        """
    )
    st.info(
        "Try it yourself: open one of each account type, then go to the "
        "**Interest** tab and run one interest cycle. Watch how the exact "
        "same button click produces three different outcomes."
    )
