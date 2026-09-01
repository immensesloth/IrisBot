import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class ThreadLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_create(self, thread):

        channel_id = await get_log_channel(thread.guild.id, "thread")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        embed = IrisEmbed.success(
            "🧵 Thread Created",
            f"Thread **{thread.name}** was created."
        )

        embed.add_field(
            name="Thread",
            value=f"{thread.name} (`{thread.id}`)",
            inline=False
        )

        if thread.parent:
            embed.add_field(
                name="Parent Channel",
                value=thread.parent.mention,
                inline=True
            )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):

        channel_id = await get_log_channel(thread.guild.id, "thread")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        embed = IrisEmbed.error(
            "🗑️ Thread Deleted",
            f"Thread **{thread.name}** was deleted."
        )

        embed.add_field(
            name="Thread",
            value=f"{thread.name} (`{thread.id}`)",
            inline=False
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):

        if (
            before.name == after.name
            and before.archived == after.archived
            and before.locked == after.locked
            and before.slowmode_delay == after.slowmode_delay
        ):
            return

        channel_id = await get_log_channel(after.guild.id, "thread")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        embed = IrisEmbed.warning(
            "✏️ Thread Updated",
            f"Thread **{after.name}** was updated."
        )

        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"`{before.name}` → `{after.name}`",
                inline=False
            )

        if before.archived != after.archived:
            embed.add_field(
                name="Archived",
                value=f"`{before.archived}` → `{after.archived}`",
                inline=True
            )

        if before.locked != after.locked:
            embed.add_field(
                name="Locked",
                value=f"`{before.locked}` → `{after.locked}`",
                inline=True
            )

        if before.slowmode_delay != after.slowmode_delay:
            embed.add_field(
                name="Slowmode",
                value=f"`{before.slowmode_delay}s` → `{after.slowmode_delay}s`",
                inline=True
            )

        await log_channel.send(
            embed=embed
        )
