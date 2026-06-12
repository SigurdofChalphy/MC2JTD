# main.py
# MAIN of MC2JTD

# Creator: @TristanofJugdral (Ver. 1.1.6 | 10 June 2026)

import discord
from discord.ext import commands
import asyncio
import time

TOKEN = input("Enter your Discord bot token: ").strip() # Type bot's token

intents = discord.Intents.default()
intents.message_content = True  # Yes, the bot reads chat
bot = commands.Bot(
    command_prefix="mc2jtd.",   # Prefix: mc2jtd.
    intents=intents,
    help_command=None
) 

# Load cogs
async def load_cogs():
    
    await bot.load_extension("cogs.msg_receive")    # Message receiver
    print("Loaded cogs/msg_receive.py")
    
    await bot.load_extension("cogs.basic_commands") # Commands
    print("Loaded cogs/basic_commands.py")
    
    await bot.load_extension("cogs.sftp_reader")    # SFTP
    print("Loaded cogs/sftp_reader.py")

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    print(f"Started at: {time.strftime('%H:%M:%S')}")
    # await bot.tree.sync() # this will be for slash-commands. Atm we're using prefixes

# Note: Make sure to load the "cogs" files before starting the bot up
async def main():
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

asyncio.run(main())
