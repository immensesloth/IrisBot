import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class MemberLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):

        # Get saved log channel
        channel_id = await get_log_channel(member.guild.id, "member")

        if not channel_id:
            return

        # Find log channel
        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        # Create embed
        embed = IrisEmbed.success(
            "👋 Member Joined",
            f"{member.mention} joined the server."
        )

        embed.add_field(
            name="User",
            value=f"{member} (`{member.id}`)",
            inline=False
        )

        embed.add_field(
            name="Account Created",
            value=discord.utils.format_dt(
                member.created_at,
                style="F"
            ),
            inline=False
        )

        embed.add_field(
            name="Member Count",
            value=str(member.guild.member_count),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        # Get saved log channel
        channel_id = await get_log_channel(member.guild.id, "member")

        if not channel_id:
            return

        # Find log channel
        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        # ==========================================
        # CHECK AUDIT LOGS
        # ==========================================

        # Check if the member was banned
        try:
            async for entry in member.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.ban
            ):
                if (
                    entry.target
                    and entry.target.id == member.id
                ):
                    return

        except discord.Forbidden:
            pass

        # Check if the member was kicked
        try:
            async for entry in member.guild.audit_logs(
                limit=5,
                action=discord.AuditLogAction.kick
            ):
                if (
                    entry.target
                    and entry.target.id == member.id
                ):
                    return

        except discord.Forbidden:
            pass

        # ==========================================
        # NORMAL MEMBER LEAVE
        # ==========================================

        embed = IrisEmbed.error(
            "🚪 Member Left",
            f"**{member}** left the server."
        )

        embed.add_field(
            name="User",
            value=f"{member} (`{member.id}`)",
            inline=False
        )

        embed.add_field(
            name="Account Created",
            value=discord.utils.format_dt(
                member.created_at,
                style="F"
            ),
            inline=False
        )

        embed.add_field(
            name="Member Count",
            value=str(member.guild.member_count),
            inline=True
        )

        await log_channel.send(
            embed=embed
        )
