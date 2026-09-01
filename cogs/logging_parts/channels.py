import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class ChannelLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        channel_id = await get_log_channel(channel.guild.id, "channel")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        embed = IrisEmbed.success(
            "📁 Channel Created",
            f"{channel.mention} was created."
        )

        embed.add_field(
            name="Channel",
            value=f"{channel.name} (`{channel.id}`)",
            inline=False
        )

        embed.add_field(
            name="Type",
            value=str(channel.type).title(),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        channel_id = await get_log_channel(channel.guild.id, "channel")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        embed = IrisEmbed.error(
            "🗑️ Channel Deleted",
            f"Channel **{channel.name}** was deleted."
        )

        embed.add_field(
            name="Channel",
            value=f"{channel.name} (`{channel.id}`)",
            inline=False
        )

        embed.add_field(
            name="Type",
            value=str(channel.type).title(),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before,
        after
    ):

        if (
            before.name == after.name
            and before.category_id == after.category_id
            and before.position == after.position
            and before.overwrites == after.overwrites
        ):
            return

        channel_id = await get_log_channel(after.guild.id, "channel")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        embed = IrisEmbed.warning(
            "✏️ Channel Updated",
            f"{after.mention} was updated."
        )

        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"`{before.name}` → `{after.name}`",
                inline=False
            )

        if before.category_id != after.category_id:
            before_category = (
                before.category.name
                if before.category
                else "None"
            )

            after_category = (
                after.category.name
                if after.category
                else "None"
            )

            embed.add_field(
                name="Category",
                value=f"`{before_category}` → `{after_category}`",
                inline=False
            )

        if before.position != after.position:
            embed.add_field(
                name="Position",
                value=f"`{before.position}` → `{after.position}`",
                inline=True
            )

        await log_channel.send(
            embed=embed
        )
