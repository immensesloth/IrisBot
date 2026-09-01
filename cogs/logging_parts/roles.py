import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class RoleLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        channel_id = await get_log_channel(role.guild.id, "role")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        embed = IrisEmbed.success(
            "🎭 Role Created",
            f"Role {role.mention} was created."
        )

        embed.add_field(
            name="Role",
            value=f"{role.name} (`{role.id}`)",
            inline=False
        )

        embed.add_field(
            name="Position",
            value=str(role.position),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        channel_id = await get_log_channel(role.guild.id, "role")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        embed = IrisEmbed.error(
            "🗑️ Role Deleted",
            f"Role **{role.name}** was deleted."
        )

        embed.add_field(
            name="Role",
            value=f"{role.name} (`{role.id}`)",
            inline=False
        )

        embed.add_field(
            name="Position",
            value=str(role.position),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_guild_role_update(
        self,
        before,
        after
    ):

        # Ignore if nothing important changed
        if (
            before.name == after.name
            and before.permissions == after.permissions
            and before.colour == after.colour
            and before.hoist == after.hoist
            and before.mentionable == after.mentionable
        ):
            return

        channel_id = await get_log_channel(after.guild.id, "role")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        embed = IrisEmbed.warning(
            "✏️ Role Updated",
            f"Role {after.mention} was updated."
        )

        if before.name != after.name:
            embed.add_field(
                name="Name",
                value=f"`{before.name}` → `{after.name}`",
                inline=False
            )

        if before.permissions != after.permissions:
            embed.add_field(
                name="Permissions",
                value="Role permissions were changed.",
                inline=False
            )

        if before.colour != after.colour:
            embed.add_field(
                name="Colour",
                value=f"`{before.colour}` → `{after.colour}`",
                inline=False
            )

        if before.hoist != after.hoist:
            embed.add_field(
                name="Hoisted",
                value=f"`{before.hoist}` → `{after.hoist}`",
                inline=True
            )

        if before.mentionable != after.mentionable:
            embed.add_field(
                name="Mentionable",
                value=f"`{before.mentionable}` → `{after.mentionable}`",
                inline=True
            )

        await log_channel.send(
            embed=embed
        )           
