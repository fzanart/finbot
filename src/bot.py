"fin bot"

import os
import logging
from datetime import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
from database.db_operations import (
    save_transaction,
    delete_transaction,
    update_transaction,
)


load_dotenv(find_dotenv())
token = os.getenv("DISCORD_TOKEN")

handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")


# @bot.event
# async def on_message(message):
#     if message.author == bot.user:
#         return

#     if "shit" in message.content.lower():
#         await message.delete()
#         await message.channel.send(f"{message.author.mention} - dont use that word!")

#     await bot.process_commands(message)


# # !hello
# @bot.command()
# async def hello(ctx):
#     await ctx.send(f"Hello {ctx.author.mention}!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Detect webhook transactions
    if "💳 **New Transaction**" in message.content:
        lines = message.content.split("\n")
        date = lines[1].split("**Date:** ")[1]
        amount = float(lines[2].split("$")[1])
        merchant = lines[3].split("**Merchant:** ")[1]
        details = lines[4].split("**Details:** ")[1]
        account_id = int(lines[5].split("**Account:** ")[1])

        txn_id = save_transaction(date, amount, merchant, details, account_id)
        await message.reply(f"✅ Transaction saved with ID: **{txn_id}**")

    await bot.process_commands(message)


@bot.command()
async def add(ctx, amount: float, merchant: str, *, details: str, account_id: int):
    """Add manual transaction: !add 50 Costco groceries"""
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    txn_id = save_transaction(date, amount, merchant, details, account_id)
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


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
