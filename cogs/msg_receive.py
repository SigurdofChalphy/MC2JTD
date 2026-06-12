# cogs/msg_receive.py
# MESSAGE RECEIVER FILE. ALSO SENDS MESSAGES ON DISCORD

# @TristanofJugdral (Ver. 1.1.6 | 10 June 2026)

from discord.ext import commands
import asyncio
import re
import data.settings as config
from utils.censor_words import censor_message

class MessageReceiver(commands.Cog):
    def __init__(self, bot):        
        self.bot = bot
        self.watch_log_task = None  # Logs tasks
        self._path_warned = False   # Check if path warning message has been sent

    async def cog_load(self):
        self.watch_log_task = asyncio.create_task(self.watch_log())

    async def cog_unload(self):
        if self.watch_log_task:
            self.watch_log_task.cancel()

    async def watch_log(self):
        await self.bot.wait_until_ready()

        # Warning message sequence
        while not self.bot.is_closed():
            if not config.LOG_PATH:
                if not self._path_warned:
                    print("LOG_PATH not set. Use mc2jtd.path to set it")
                    self._path_warned = True
                await asyncio.sleep(5)
                continue
            self._path_warned = False
        
            try:
                with open(config.LOG_PATH, "r", encoding="utf-8") as fileLogs:
                    fileLogs.seek(0, 2)  # Jump to the end of the file (a.k.a newest)

                    while not self.bot.is_closed():
                        line = fileLogs.readline() # This is the message being sent

                        if line:
                            channel = self.bot.get_channel(config.CHANNEL_ID)

                            # check if channel is legit
                            if channel is None:
                                print(f"Could not find channel ID: {config.CHANNEL_ID}")
                                await asyncio.sleep(2)
                                continue

                            # Read PLAYER messages
                            playerMatch = re.search(r'\[CHAT\] <(\w+)> (.+)', line)
                            if playerMatch and config.settings["showPlayerMessages"]:

                                # NAME (anonymous check)
                                username = playerMatch.group(1)
                                if config.settings["anonymousMode"]:
                                    username = ""
                                
                                # MESSAGE (censor check)
                                message = playerMatch.group(2)
                                if config.settings["censorEnabled"]:
                                    message = censor_message(message, config.FILTERED_PLAYER)
                            
                                await channel.send(f"**{username}**: {message}")

                            # Read SYSTEM messages
                            systemMatch = re.search(r'\[System\] \[CHAT\] (.+)', line)

                            if systemMatch and config.settings["showSystemMessages"]:
                                message = systemMatch.group(1)

                                # Remove Minecraft color codes like §6, §r, etc.
                                message = re.sub(r'§.', '', message)

                                # Censor (if allowed)
                                if config.settings["censorEnabled"]:
                                    message = censor_message(message, config.FILTERED_SYSTEM)

                                # Check notification event type
                                eventAllowed = False

                                if "spawned" in message and config.settings["showSpawns"]:
                                    eventAllowed = True

                                elif "despawned" in message and config.settings["showDespawns"]:
                                    eventAllowed = True

                                elif "captured" in message and config.settings["showCaptures"]:
                                    eventAllowed = True

                                if not eventAllowed:
                                    await asyncio.sleep(0.5)
                                    continue

                                shinyIcon = ""
                                rarityIcon = ""

                                presentTraits = [] # Present categories go here

                                # Shiny category
                                if "Shiny" in message:
                                    shinyIcon = "✨"
                                    presentTraits.append("showShiny")

                                # Rarity categories
                                if "Legendary" in message:
                                    rarityIcon = "🔴"
                                    presentTraits.append("showLegendary")

                                elif "Ultra Beast" in message:
                                    rarityIcon = "🟣"
                                    presentTraits.append("showUltraBeast")

                                elif "Paradox" in message:
                                    rarityIcon = "🟡"
                                    presentTraits.append("showParadox")

                                # Send it if ANY matching category is enabled, otherwise it won't send for one being false
                                # e.g, shiny and paradox still sends if paradox is enabled, even if shiny is disabled
                                if presentTraits:
                                    specialAllowed = any(
                                        config.settings[key] for key in presentTraits
                                    )
                                else:
                                    specialAllowed = True

                                if specialAllowed:
                                    await channel.send(f"{shinyIcon}{rarityIcon} *{message}*") # send message WITH tags

                        await asyncio.sleep(0.5) # Wait

            except FileNotFoundError:
                print(f"Log file not found: {config.LOG_PATH}")

async def setup(bot):
    await bot.add_cog(MessageReceiver(bot))
