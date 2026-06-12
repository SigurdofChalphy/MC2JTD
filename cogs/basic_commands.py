# cogs/basic_commands.py
# BASIC COMMANDS using "mc2jtd." prefix on Discord (see main.py)

# @TristanofJugdral (Ver. 1.2.8 | 11 June 2026)

import discord
from discord.ext import commands
import data.settings as config
import asyncio
import time
from data.settings import start_time
import os

# 1. Authorisation check
def is_authorised():
    async def predicate(ctx):
        if ctx.author.guild_permissions.administrator:
            return True
        return any(role.name in config.AUTHORISED_ROLES for role in ctx.author.roles)
    return commands.check(predicate)

# 2. List of commands
class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==== ctx: stands for "context"; Discord variable ====
    # ctx.author        = Message's user
    # ctx.channel       = Reference message's channel
    # ctx.guild         = Discord server
    # ctx.send("abc")   = Send a reply message "abc"
    # discord.DMChannel = Reference user's DMs
    
    # .help - list of commands
    @commands.command(name="help")
    async def help(self, ctx):
        await ctx.send(
            "**MC2JTD Commands List**\n"
            "`=========== GENERAL ===========\n`"
            "`mc2jtd.help` - List of commands\n"
            "`mc2jtd.status` - Check if the server is running\n"
            "`mc2jtd.channel` - Set Discord message channel\n"
            "`========== ADMIN ONLY =========\n`"
            "`mc2jtd.restart` - Refresh code if updates are needed\n"
            "`mc2jtd.kill` - **Shut down** bot from computer\n"
            "`mc2jtd.path` - Set file path to chat/system logs\n"
            "`mc2jtd.notifications` - Toggle specific notifications\n"
            "`mc2jtd.addrole` - Authorise a new role\n"
            "`mc2jtd.removerole` - Remove an authorised role\n"
            "`mc2jtd.sftp` - Configure server SFTP\n"
            "`--> mc2jtd.sftp [host, port, username, password, path, connect]`\n"
            "`---------- TOGGLES -----------`\n"
            "`mc2jtd.playermsg` - Toggle PLAYER messages on/off\n"
            "`mc2jtd.systemmsg` - Toggle SYSTEM messages on/off\n"
            "`mc2jtd.censor` - Toggle profanity filter on/off\n"
            "`mc2jtd.anonymous` - Toggle anonymous mode on/off\n"
        )

        
    # .addrole - Authorise a new role
    @is_authorised() # !! admin only
    @commands.command(name="addrole")
    async def addrole(self, ctx, *, role_name: str):
        if role_name not in config.AUTHORISED_ROLES:
            config.AUTHORISED_ROLES.append(role_name)
            config.save_config()
            await ctx.send(f"`{role_name}` has been added to `authorised roles`")
        else:
            await ctx.send(f"`{role_name}` is already authorised")


    # .anonymous - toggle anonymous mode
    @is_authorised() # !! admin only
    @commands.command(name="anonymous")
    async def anonymous(self, ctx):
        config.settings["anonymousMode"] = not config.settings["anonymousMode"]
        state = "enabled" if config.settings["anonymousMode"] else "disabled"
        await ctx.send(f"Anonymous mode: `{state}`")


    # .censor - toggle message filter (see settings/FILTERED_PLAYER)
    @is_authorised() # !! admin only
    @commands.command(name="censor")
    async def censor(self, ctx):
        config.settings["censorEnabled"] = not config.settings["censorEnabled"]
        state = "enabled" if config.settings["censorEnabled"] else "disabled"
        await ctx.send(f"Profanity filter: `{state}`")


    # .channel - set Discord message channel
    @is_authorised() # !! admin only
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


    # .kill - shut down the bot
    @commands.command(name="kill")
    @commands.is_owner()
    async def kill(self, ctx):
        await ctx.send("Shutting down...")
        await self.bot.close()

    @kill.error
    async def kill_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("Only the bot owner can do that.")


    # .notifications - toggle specific notification types
    @is_authorised() # !! admin only
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
            await ctx.send(f"{kind} notifications: `{state}`")
        else:
            await ctx.send(f"Unknown notification type `{kind}`. Options: {', '.join(options.keys())}")

    
    # .path - set server log file path
    @is_authorised() # !! admin only
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


    # .playermsg - toggle player messages
    @is_authorised() # !! admin only
    @commands.command(name="playermsg")
    async def playermsg(self, ctx):
        config.settings["showPlayerMessages"] = not config.settings["showPlayerMessages"]
        state = "enabled" if config.settings["showPlayerMessages"] else "disabled"
        await ctx.send(f"Show player messages: `{state}`")


    # .removerole - Remove a previously authorised role
    @is_authorised() # !! admin only
    @commands.command(name="removerole")
    async def removerole(self, ctx, *, role_name: str):
        if role_name in config.AUTHORISED_ROLES:
            config.AUTHORISED_ROLES.remove(role_name)
            config.save_config()
            await ctx.send(f"`{role_name}` has been removed from `authorised roles`")
        else:
            await ctx.send(f"`{role_name}` is not an authorised role")


    # .restart - refresh code
    @is_authorised() # !! admin only
    @commands.command(name="restart")
    async def restart(self, ctx):

        # Restart message_receiver
        receiver = self.bot.cogs.get("MessageReceiver")
        if receiver:
            if receiver.watch_log_task:
                receiver.watch_log_task.cancel()
            receiver.watch_log_task = asyncio.create_task(receiver.watch_log())

        # Restart SFTP_reader
        sftp = sftp = self.bot.cogs.get("SFTPReader")
        if sftp:
            if sftp.watch_task:
                sftp.watch_task.cancel()
            sftp.disconnect()
            sftp._connect_attempts = 0  # Reset (attempts --> 0/3)
            sftp.watch_task = asyncio.create_task(sftp.watch_log())
            
        if receiver or sftp:
            await ctx.send("MC2JTD has been successfully restarted")
        else:
            await ctx.send("ERROR: Some cogs not found for restart")


    # .sftp - configure SFTP (server stuff)
    @is_authorised() # !! admin only
    @commands.command(name="sftp")
    async def sftp(self, ctx, setting: str = None, *, value: str = None):
        """
        Configure SFTP settings.
        setting = which field to update (host, port, username, password, path, connect)
        value = what you want that value set to
        """
        if setting is None:
            # Show current SFTP status without revealing password
            await ctx.send(
                f"**SFTP Settings:**\n"
                f"`host`: {config.SFTP_HOST or 'Not set'}\n"
                f"`port`: {config.SFTP_PORT}\n"
                f"`path`: {config.SFTP_LOG_PATH}\n"
                f"`username`: {config.SFTP_USERNAME or 'Not set'}\n"
                f"`password`: {'Set' if config.SFTP_PASSWORD else 'Not set'}\n"
            )
            return

        setting = setting.lower()

        # ".is_empty()" check
        if setting != "connect" and value is None:
            await ctx.send(f"Please provide a value for `{setting}`.")
            return

        # Setting options:
        # { "host", "port", "path", "username", "password", "connect" }
        
        if setting == "host":
            config.SFTP_HOST = value
            await ctx.send(f"SFTP host set to `{value}`")
            
        elif setting == "port":
            try:
                config.SFTP_PORT = int(value)
            except ValueError:
                await ctx.send("SFTP port must be a number.")
                return

            await ctx.send(f"SFTP port set to `{value}`")
            
        elif setting == "username":
            config.SFTP_USERNAME = value
            await ctx.send(f"SFTP username set to `{value}`")
            
        elif setting == "password":
            config.SFTP_PASSWORD = value
            await ctx.send(f"SFTP password received") 
            await ctx.message.delete()  # Deletes message automatically to hide password
            
        elif setting == "path":
            config.SFTP_LOG_PATH = value
            await ctx.send(f"SFTP log path set to `{value}`")
            
        elif setting == "connect":

            # Restart the SFTPReader cog to trigger a new connection
            sftp_cog = self.bot.cogs.get("SFTPReader") 

            if sftp_cog:
                
                if sftp_cog.watch_task:
                    sftp_cog.watch_task.cancel()

                sftp_cog.disconnect()
                sftp_cog.watch_task = asyncio.create_task(sftp_cog.watch_log())
                
                await ctx.send("Attempting SFTP connection...")
            else:
                await ctx.send("SFTPReader cog not found.")
            return
        
        else:
            await ctx.send(
                "ERROR: Unknown setting. Options: "
                "`host` `port` `username` `password` `path` `connect`"
            )
            return

        config.save_config()


    # .status - return server status
    @commands.command(name="status")
    async def status(self, ctx):

        # Checking LOG_PATH (SFTP):
        if config.SFTP_HOST:
            sftp_cog = self.bot.cogs.get("SFTPReader")
            if sftp_cog and sftp_cog.connected:
                await ctx.send("SFTP is connected and reading server logs")
            else:
                await ctx.send("SFTP is **not** connected. Use `mc2jtd.sftp connect`")
            return
        
        # Checking LOG_PATH (LOCAL):
        if not config.LOG_PATH:
            await ctx.send("Log path not set. Use `mc2jtd.path` to set it")
            return
        
        # See if the server has been active within 5 minutes:
        if os.path.exists(config.LOG_PATH):
            reference_time = os.path.getmtime(config.LOG_PATH) # (now).time - (previous msg).time
        else:
            reference_time = start_time 
            
        msg_minutes_ago = int(time.time() - reference_time) // 60
        if msg_minutes_ago < 5:
            await ctx.send(f"Server appears to be running. Last log update: `{msg_minutes_ago}` minutes ago")
        else:
            await ctx.send(f"Server may be offline. Last log update: `{msg_minutes_ago}` minutes ago")

    # .systemmsg - toggle system messages
    @is_authorised() # !! admin only
    @commands.command(name="systemmsg")
    async def systemmsg(self, ctx):
        config.settings["showSystemMessages"] = not config.settings["showSystemMessages"]
        state = "enabled" if config.settings["showSystemMessages"] else "disabled"
        await ctx.send(f"Show system messages: `{state}`")

        
            
async def setup(bot):
    await bot.add_cog(BasicCommands(bot))

