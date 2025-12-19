"""Module for database operations related to financial transactions."""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "transactions.db")


def save_transaction(date, amount, merchant, details, account_id, source="manual"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """INSERT INTO transactions (date, amount, merchant, details, account_id, created_at, source)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            date,
            amount,
            merchant,
            details,
            account_id,
            datetime.now().isoformat(),
            source,
        ),
    )
    txn_id = c.lastrowid
    conn.commit()
    conn.close()
    return txn_id


def delete_transaction(txn_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    conn.close()


def update_transaction(txn_id, field, value):
    """Update a specific field of a transaction."""
    allowed_fields = ["category", "merchant", "details", "amount", "date"]

    if field.lower() not in allowed_fields:
        raise ValueError(f"Invalid field. Allowed: {', '.join(allowed_fields)}")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Handle amount as float
    if field.lower() == "amount":
        value = float(value)

    c.execute(f"UPDATE transactions SET {field} = ? WHERE id = ?", (value, txn_id))
    conn.commit()
    conn.close()


def get_monthly_expenses_by_source():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    month_prefix = datetime.now().strftime("%Y-%m")
    c.execute(
        """SELECT source, SUM(amount)
           FROM transactions
           WHERE strftime('%Y-%m', created_at) = ?
           GROUP BY source""",
        (month_prefix,),
    )
    expenses = {row[0]: row[1] for row in c.fetchall()}
    conn.close()
    return expenses
