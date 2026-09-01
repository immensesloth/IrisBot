import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class ServerLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):

        # Get log channel
        channel_id = await get_log_channel(after.id, "server")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        # ==========================================
        # SERVER NAME
        # ==========================================

        if before.name != after.name:

            embed = IrisEmbed.warning(
                "📝 Server Name Changed",
                f"The server name was changed."
            )

            embed.add_field(
                name="Before",
                value=before.name,
                inline=True
            )

            embed.add_field(
                name="After",
                value=after.name,
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

        # ==========================================
        # SERVER ICON
        # ==========================================

        if before.icon != after.icon:

            embed = IrisEmbed.warning(
                "🖼️ Server Icon Changed",
                "The server icon was changed."
            )

            if after.icon:
                embed.set_thumbnail(
                    url=after.icon.url
                )

            await log_channel.send(
                embed=embed
            )

        # ==========================================
        # VERIFICATION LEVEL
        # ==========================================

        if before.verification_level != after.verification_level:

            embed = IrisEmbed.warning(
                "🔐 Verification Level Changed",
                "The server verification level was changed."
            )

            embed.add_field(
                name="Before",
                value=str(
                    before.verification_level
                ).title(),
                inline=True
            )

            embed.add_field(
                name="After",
                value=str(
                    after.verification_level
                ).title(),
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

        # ==========================================
        # DEFAULT NOTIFICATION LEVEL
        # ==========================================

        if (
            before.default_notifications
            != after.default_notifications
        ):

            embed = IrisEmbed.warning(
                "🔔 Notification Settings Changed",
                "The server's default notification settings were changed."
            )

            embed.add_field(
                name="Before",
                value=str(
                    before.default_notifications
                ).title(),
                inline=True
            )

            embed.add_field(
                name="After",
                value=str(
                    after.default_notifications
                ).title(),
                inline=True
            )

            await log_channel.send(
                embed=embed
            )
