# BASIC COMMANDS
# @TristanofJugdral

import discord
from discord.ext import commands
import data.settings as config
import os

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # /help - list of commands
    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send(
            "**MC2JTD Commands**\n"
            "`mc2jtd.help` - List of commands\n"
            "`mc2jtd.status` - Check if the server is running\n"
            "`mc2jtd.kill` - shut down bot from computer\n"
            "`mc2jtd.channel` - Set Discord message channel\n"
            "`mc2jtd.path` - Set file path to chat/system logs\n"
            "`mc2jtd.restart` - Refresh code if updates are needed\n"
            "`mc2jtd.playermsg` - Toggle player messages on/off\n"
            "`mc2jtd.systemmsg` - Toggle system messages on/off\n"
            "`mc2jtd.censor` - Toggle profanity filter on/off\n"
            "`mc2jtd.anonymous` - Toggle anonymous mode on/off\n"
            "`mc2jtd.notifications` - Toggle specific notifications\n"
        )

    # /status - return server status
    @commands.command(name="status")
    async def status(self, ctx):
        log_exists = os.path.exists(config.LOG_PATH)
        if log_exists:
            await ctx.send(f"Server appears to be running")
        else:
            await ctx.send(f"ERROR: Server logs not found.")
            
    # /kill - shut down the bot
    @commands.command(name="kill")
    @commands.is_owner()
    async def kill(self, ctx):
        await ctx.send("Shutting down...")
        await self.bot.close()
        os.kill(os.getpid(), 9) # Force kill

    @kill.error
    async def kill_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("Only the bot owner can do that.")
            
    # /channel - set Discord message channel
    @commands.command(name="channel")
    async def channel(self, ctx, channel: discord.TextChannel = None):
        if channel is None:
            channel = ctx.channel # default
            
        # Check "send messages" permissions
        permissions = channel.permissions_for(ctx.guild.me)
        if not permissions.send_messages:
            await ctx.send(f"Missing permission to send messages in {channel.mention}.")
            return
        
        config.CHANNEL_ID = channel.id
        config.save_config() # ** Store ID for next time
        await ctx.send(f"Messages will now be sent to {channel.mention}.")

    @channel.error
    async def channel_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(
                "Invalid channel. Please provide a valid text channel ID or mention.\n"
            )
        else:
            raise error
        
    # /path - set server log file path
    @commands.command(name="path")
    async def path(self, ctx, *, path: str = None):
        if path is None:
            await ctx.send(f"Current log path:\n`{config.LOG_PATH}`")
            return

        path = path.strip()

        # Accept Python-style raw string input: r"C:\..."
        if path.startswith('r"') or path.startswith("r'"):
            path = path[1:]

        # Remove surrounding quotes
        path = path.strip().strip('"').strip("'")

        if not os.path.exists(path):
            await ctx.send(
                "That file path does not exist.\n"
                "Make sure you provide the full path to `latest.log`."
            )
            return

        if not path.endswith("latest.log"):
            await ctx.send(
                "That path exists, but it does not look like `latest.log`."
            )
            return

        config.LOG_PATH = path
        config.save_config() # ** Store path for next time
        await ctx.send(f"Log path updated:\n`{config.LOG_PATH}`")

    # /restart - refresh code
    @commands.command(name="restart")
    @commands.is_owner()
    async def restart(self, ctx):
        receiver = self.bot.cogs.get("MessageReceiver")
        await ctx.send("Restarting...")
        if receiver:
            if receiver.watch_log_task:
                receiver.watch_log_task.cancel()
            receiver.watch_log_task = asyncio.create_task(receiver.watch_log())
            await ctx.send("Message Receider cog has been restarted")
        else:
            await ctx.send("Message Receiver cog not found...")
    
    # /playermsg - toggle player messages
    @commands.command(name="playermsg")
    async def playermsg(self, ctx):
        config.settings["showPlayerMessages"] = not config.settings["showPlayerMessages"]
        state = "enabled" if config.settings["showPlayerMessages"] else "disabled"
        await ctx.send(f"Show player messages: {state}")

    # /systemmsg - toggle system messages
    @commands.command(name="systemmsg")
    async def systemmsg(self, ctx):
        config.settings["showSystemMessages"] = not config.settings["showSystemMessages"]
        state = "enabled" if config.settings["showSystemMessages"] else "disabled"
        await ctx.send(f"Show system messages: {state}")

    # /censor - toggle message filter (see settings/FILTERED_PLAYER)
    @commands.command(name="censor")
    async def censor(self, ctx):
        config.settings["censorEnabled"] = not config.settings["censorEnabled"]
        state = "enabled" if config.settings["censorEnabled"] else "disabled"
        await ctx.send(f"Profanity filter: {state}")

    # /anonymous - toggle anonymous mode
    @commands.command(name="anonymous")
    async def anonymous(self, ctx):
        config.settings["anonymousMode"] = not config.settings["anonymousMode"]
        state = "enabled" if config.settings["anonymousMode"] else "disabled"
        await ctx.send(f"Anonymous mode: {state}")

    # /notifications - toggle specific notification types
    @commands.command(name="notifications")
    async def notifications(self, ctx, kind: str = None):
        # Note: the "kind" variable is optional. It's used if you're looking at a specific option
        options = {
            "spawns": "showSpawns",
            "despawns": "showDespawns",
            "captures": "showCaptures",
            "legendary": "showLegendary",
            "ultrabeast": "showUltraBeast",
            "paradox": "showParadox",
            "shiny": "showShiny",
        }
        
        if kind is None:
            # Print current status for EACH notifications
            status_lines = "\n".join(
                f"`{k}`: {'TRUE' if config.settings[v] else 'FALSE'}"
                for k, v in options.items()
            )
            await ctx.send(f"**Notification Settings:**\n{status_lines}")
        elif kind.lower() in options:
            key = options[kind.lower()] # I turned off case sensitive
            config.settings[key] = not config.settings[key]
            state = "enabled" if config.settings[key] else "disabled"
            await ctx.send(f"{kind} notifications {state}")
        else:
            await ctx.send(f"Unknown notification type `{kind}`. Options: {', '.join(options.keys())}")

async def setup(bot):
    await bot.add_cog(BasicCommands(bot))
