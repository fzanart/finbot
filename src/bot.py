"fin bot"

import os
import sys
import json
import subprocess
import logging
from time import time
from datetime import datetime
import yaml
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
from database.db_operations import (
    save_transaction,
    delete_transaction,
    update_transaction,
    get_monthly_expenses_by_source,
)
from LlmsOperations import parse_mail_message


load_dotenv(find_dotenv())
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

with open("src/database/accounts.yml", "r") as f:
    accounts = yaml.safe_load(f)
    CARD_MAPPING = accounts["card_mapping"]


@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Code update command
    if message.content.strip() == "!deploy":
        await message.channel.send("Pulling latest code and restarting...")
        subprocess.run(["git", "pull", "origin", "main"], cwd="/opt/finbot")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    if message.content.startswith("!parse_email"):
        try:
            command_line, email_body = message.content.split("\n", 1)
            message_id = command_line.split()[1]
            await process_and_save_email(message, message_id, email_body)
        except Exception as e:
            await message.reply(f"❌ Error processing webhook email: {str(e)}")
        return

    # Detect webhook transactions
    if "💳 **New Transaction**" in message.content:

        txn = parse_wallet_transaction(message.content)

        account_number = CARD_MAPPING.get(txn["account_id"].lower(), "Unknown")
        txn["account_id"] = account_number

        txn_id = save_transaction(**txn)
        expenses = get_monthly_expenses_by_source()
        await message.reply(
            f"✅ Transaction saved with ID: **{txn_id}**\n"
            f"Webhook total expenses: **${expenses.get('webhook', 0):,d}**\n"
            f"Email total expenses: **${expenses.get('email', 0):,d}**"
        )

    await bot.process_commands(message)


def parse_wallet_transaction(content: str) -> dict:
    lines = content.splitlines()
    get = lambda i: lines[i].partition("** ")[2]

    return {
        "date": get(1),
        "amount": float(get(2).lstrip("$")),
        "merchant": get(3),
        "details": get(4),
        "account_id": get(5),
        "source": "webhook",
    }


@bot.command()
async def add(ctx, amount: float, merchant: str, *, details: str, account_id: int):
    """Add manual transaction: !add 50 Costco groceries"""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txn_id = save_transaction(date, amount, merchant, details, account_id, "manual")
    await ctx.reply(f"✅ Manual transaction saved with ID: **{txn_id}**")


@bot.command()
async def delete(ctx, txn_id: int):
    """Delete transaction: !delete 5"""
    delete_transaction(txn_id)
    await ctx.reply(f"🗑️ Transaction {txn_id} deleted")


@bot.command()
async def update(ctx, txn_id: int, field: str, *, value: str):
    """Update transaction field: !update 5 category food"""
    try:
        update_transaction(txn_id, field, value)
        await ctx.reply(f"✅ Transaction {txn_id} updated: **{field}** = {value}")
    except ValueError as e:
        await ctx.reply(f"❌ {str(e)}")


async def process_and_save_email(reply_target, message_id: str, message_content: str):
    """Helper function to parse, save, and reply for an email message."""
    try:
        r = json.loads(parse_mail_message(message_content))
        amount = float(r.get("amount"))
        if amount == 0:
            await reply_target.reply(
                f"❌ Email transaction disregarded as amount is 0 - Details: {r.get('details')}"
            )
            return

        txn_id = save_transaction(
            r.get("date"),
            amount,
            r.get("merchant"),
            f"{message_id} - {r.get('details')}",
            r.get("account"),
            "email",
        )

        await reply_target.reply(
            f"✅ Email parsed and transaction saved with ID: **{txn_id}**"
        )

    except Exception as e:
        await reply_target.reply(f"❌ Error parsing email: {str(e)}")


@bot.command()
async def parse_email(ctx, message_id: str, *, message_content: str):
    """Parse email message: !parse_email 19abacc9a8b5ee7b .... message content ...."""
    await process_and_save_email(ctx, message_id, message_content)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
