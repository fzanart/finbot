"test script to send fake tx to discord"

import os
import random
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# Sample data
merchants = [
    "Starbucks",
    "Uber",
    "Whole Foods",
    "Shell Gas",
    "Netflix",
    "Amazon",
    "McDonald's",
]
details = [
    "Coffee",
    "Ride to work",
    "Groceries",
    "Gas",
    "Subscription",
    "Online shopping",
    "Lunch",
]


def send_transaction():
    transaction = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Amount": round(random.uniform(5.0, 150.0), 2),
        "Merchant": random.choice(merchants),
        "Details": random.choice(details),
        "AccountID": random.randint(1, 3),  # Assumes you have accounts 1-3
    }

    # Format as Discord message
    message = {
        "content": f"💳 **New Transaction**\n"
        f"**Date:** {transaction['Date']}\n"
        f"**Amount:** ${transaction['Amount']}\n"
        f"**Merchant:** {transaction['Merchant']}\n"
        f"**Details:** {transaction['Details']}\n"
        f"**Account:** {transaction['AccountID']}"
    }

    response = requests.post(WEBHOOK_URL, json=message)
    print(f"Sent: {transaction}")
    print(f"Status: {response.status_code}")


if __name__ == "__main__":
    send_transaction()
