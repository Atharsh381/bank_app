# PyBank — OOP Banking Application (Streamlit)

An end-to-end demo banking app built to clearly showcase the **4 pillars
of Object-Oriented Programming** in a real, runnable project.

## Project structure

```
bank_app/
├── .vscode/
│   ├── launch.json   # F5 in VS Code runs `streamlit run app.py`
│   └── settings.json
├── .gitignore
├── models.py          # Domain classes: BankAccount (abstract) + 3 subclasses
├── bank.py            # Bank manager class: operations + JSON persistence
├── app.py             # Streamlit UI (thin layer, calls into bank.py)
├── requirements.txt
├── README.md
└── bank_data.json     # auto-created on first run — your "database"
```

## How to open in VS Code

1. Unzip `bank_app.zip` (or clone/copy the folder) anywhere on your machine.
2. In VS Code: **File → Open Folder…** → select the `bank_app` folder.
3. (Recommended) Create a virtual environment so dependencies stay isolated:
   ```bash
   python -m venv .venv
   # macOS/Linux:
   source .venv/bin/activate
   # Windows:
   .venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Pick the `.venv` interpreter in VS Code (bottom-right of the window, or
   `Ctrl+Shift+P` → "Python: Select Interpreter").
6. Run the app either way:
   - **Terminal**: `streamlit run app.py`
   - **VS Code Run & Debug panel**: select "Streamlit: Run app.py" and press F5
     (config already included in `.vscode/launch.json`)
7. Open the URL Streamlit prints (usually http://localhost:8501).

## How to run (without VS Code)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## The 4 pillars, mapped to code

| Pillar | File / Class | How |
|---|---|---|
| **Encapsulation** | `models.py` → `BankAccount` | `__balance`, `__pin_hash`, `__transactions` are private attributes. They can only change through validated methods (`deposit()`, `withdraw()`, `change_pin()`) — never set directly. |
| **Abstraction** | `models.py` → `class BankAccount(ABC)` | Declares `withdraw()`, `calculate_interest()`, `account_type()` as `@abstractmethod`. The class cannot be instantiated on its own — Python enforces that every real account type supplies its own implementation. |
| **Inheritance** | `SavingsAccount`, `CurrentAccount`, `FixedDepositAccount` | All three inherit shared behaviour (deposits, balance tracking, PIN handling, transaction logging) from `BankAccount`. |
| **Polymorphism** | `bank.py` → `Bank.withdraw()`, `Bank.run_interest_cycle()` | These call `account.withdraw(...)` / `account.calculate_interest()` on a variable typed only as `BankAccount`. The actual method that runs depends on the object's real subclass at runtime. |

The app's **"OOP Explainer"** tab repeats this table inside the UI itself,
and the **"Interest"** tab is the best live demo: one button click calls
the same method on every account, but Savings/Fixed-Deposit accounts earn
interest while Current accounts correctly earn ₹0.

## Features implemented

- Open an account (Savings / Current / Fixed Deposit), each with its own
  interest rate and withdrawal rules
- PIN-based login (SHA-256 hashed — demo-grade, not production security)
- Deposit, withdraw, transfer between accounts
- Per-account transaction statement
- Bank-wide interest cycle (polymorphic dispatch)
- Admin view of all accounts
- Data persists to `bank_data.json` between runs (no external DB needed)

## Honest limitations (please read)

- **Security**: PINs are hashed with plain SHA-256 and no salt. This is
  fine for a learning project but is **not** how a real bank should store
  credentials (use bcrypt/argon2, plus proper session/auth handling).
- **Persistence**: uses a flat JSON file, not a real database. Fine for a
  demo; a production system would use SQLite/Postgres with transactions.
- **Concurrency**: not designed for multiple simultaneous users writing
  at once (no file locking).
- I tested account creation, deposit, withdrawal rules (including the
  savings minimum balance, current-account overdraft limit, and
  fixed-deposit withdrawal block), transfers, interest cycling,
  authentication, abstract-class enforcement, and JSON reload — all
  passed in my test run. I did not test every possible edge case (e.g.
  concurrent users, malformed JSON recovery beyond a basic try/except),
  so please verify further before using this for anything beyond
  learning/demo purposes.
