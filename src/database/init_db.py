"""One-time database initialization script."""

import sqlite3
from datetime import datetime
from pathlib import Path
import yaml


def init_db():
    """Create database tables and load initial accounts from YAML."""

    # Delete existing database
    db_path = Path("transactions.db")
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect("transactions.db")
    c = conn.cursor()

    # Accounts table
    c.execute(
        """CREATE TABLE accounts
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              bank TEXT,
              account_type TEXT CHECK(account_type IN ('Debit', 'Credit', 'Savings')),
              currency TEXT,
              account_number TEXT,
              balance REAL DEFAULT 0,
              credit_limit REAL DEFAULT 0,
              updated_at TEXT)"""
    )

    # Transactions table
    c.execute(
        """CREATE TABLE transactions
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              date TEXT,
              amount REAL,
              merchant TEXT,
              details TEXT,
              category TEXT,
              account_id INTEGER,
              created_at TEXT,
              FOREIGN KEY (account_id) REFERENCES accounts(id))"""
    )

    conn.commit()

    # Load accounts from YAML
    with open("accounts.yml", "r") as f:
        config = yaml.safe_load(f)

    for acc in config["accounts"]:
        c.execute(
            """INSERT INTO accounts 
               (bank, account_type, currency, account_number, balance, credit_limit, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                acc["bank"],
                acc["type"],
                acc["currency"],
                acc.get("number", ""),
                acc.get("balance", 0),
                acc.get("credit_limit", 0),
                datetime.now().isoformat(),
            ),
        )

    conn.commit()
    conn.close()
    print(f"✅ Database created with {len(config['accounts'])} accounts")


if __name__ == "__main__":
    init_db()
