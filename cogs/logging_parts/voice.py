import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class VoiceLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member,
        before,
        after
    ):

        # Ignore bots
        if member.bot:
            return

        # Ignore if nothing relevant changed
        if (
            before.channel == after.channel
            and before.mute == after.mute
            and before.deaf == after.deaf
            and before.self_mute == after.self_mute
            and before.self_deaf == after.self_deaf
        ):
            return

        # Get saved log channel
        channel_id = await get_log_channel(member.guild.id, "voice")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        if log_channel is None:
            return

        # ==========================================
        # JOIN VOICE
        # ==========================================

        if before.channel is None and after.channel is not None:

            embed = IrisEmbed.success(
                "🎤 Voice Channel Joined",
                f"{member.mention} joined {after.channel.mention}."
            )

            embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            embed.add_field(
                name="Channel",
                value=after.channel.mention,
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

            return

        # ==========================================
        # LEAVE VOICE
        # ==========================================

        if before.channel is not None and after.channel is None:

            embed = IrisEmbed.error(
                "🚪 Voice Channel Left",
                f"{member.mention} left {before.channel.mention}."
            )

            embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            embed.add_field(
                name="Channel",
                value=before.channel.mention,
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

            return

        # ==========================================
        # MOVE VOICE CHANNEL
        # ==========================================

        if (
            before.channel is not None
            and after.channel is not None
            and before.channel != after.channel
        ):

            embed = IrisEmbed.warning(
                "🔀 Voice Channel Moved",
                f"{member.mention} moved voice channels."
            )

            embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            embed.add_field(
                name="From",
                value=before.channel.mention,
                inline=True
            )

            embed.add_field(
                name="To",
                value=after.channel.mention,
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

            return

        # ==========================================
        # SERVER MUTE / DEAFEN
        # ==========================================

        if before.mute != after.mute:

            action = "Muted" if after.mute else "Unmuted"

            embed = IrisEmbed.warning(
                f"🔇 Member {action}",
                f"{member.mention} was {action.lower()}."
            )

            embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            embed.add_field(
                name="Channel",
                value=(
                    after.channel.mention
                    if after.channel
                    else "Not in voice"
                ),
                inline=True
            )

            await log_channel.send(
                embed=embed
            )

        # ==========================================
        # SERVER DEAFEN / UNDEAFEN
        # ==========================================

        if before.deaf != after.deaf:

            action = "Deafened" if after.deaf else "Undeafened"

            embed = IrisEmbed.warning(
                f"🔇 Member {action}",
                f"{member.mention} was {action.lower()}."
            )

            embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            embed.add_field(
                name="Channel",
                value=(
                    after.channel.mention
                    if after.channel
                    else "Not in voice"
                ),
                inline=True
            )

            await log_channel.send(
                embed=embed
            )
