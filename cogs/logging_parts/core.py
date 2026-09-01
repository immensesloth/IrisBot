import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel,
    set_all_log_channels,
)


class LoggingCore(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # SET LOG
    # ==========================================

    @app_commands.command(
        name="setlog",
        description="Set the logging channel."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def setlog(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        await set_log_channel(
            interaction.guild.id,
            channel.id
        )

        embed = IrisEmbed.success(
            "📜 Logging Enabled",
            f"Log channel set to {channel.mention}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # LOG STATUS
    # ==========================================

    @app_commands.command(
        name="logstatus",
        description="Shows the current log channel."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def logstatus(
        self,
        interaction: discord.Interaction
    ):

        channel_id = await get_log_channel(
            interaction.guild.id
        )

        if not channel_id:
            return await interaction.response.send_message(
                "❌ No log channel has been set.",
                ephemeral=True
            )

        channel = interaction.guild.get_channel(
            channel_id
        )

        if channel is None:
            return await interaction.response.send_message(
                "❌ The saved log channel no longer exists.",
                ephemeral=True
            )

        embed = IrisEmbed.success(
            "📜 Logging Status",
            f"Current log channel: {channel.mention}"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # REMOVE LOG
    # ==========================================

    @app_commands.command(
        name="removelog",
        description="Remove the logging channel."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def removelog(
        self,
        interaction: discord.Interaction
    ):

        await remove_log_channel(
            interaction.guild.id
        )

        embed = IrisEmbed.success(
            "📜 Logging Disabled",
            "The logging channel has been removed."
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # SETUP ALL LOG CHANNELS
    # ==========================================

    @app_commands.command(
        name="setup-logs",
        description="Create and configure all logging channels."
    )
    @app_commands.checks.has_permissions(
        administrator=True
    )
    async def setup_logs(
        self,
        interaction: discord.Interaction
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        guild = interaction.guild

        if guild is None:
            return await interaction.followup.send(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        # ==========================================
        # FIND / CREATE CATEGORY
        # ==========================================

        category = discord.utils.get(
            guild.categories,
            name="SERVER LOGS"
        )

        if category is None:
            category = await guild.create_category(
                "SERVER LOGS",
                reason="Iris logging setup"
            )

        # ==========================================
        # LOG CHANNELS
        # ==========================================

        log_channels = {
            "mod": "🛡️・mod-logs",
            "message": "💬・message-logs",
            "member": "👥・member-logs",
            "role": "🎭・role-logs",
            "channel": "📁・channel-logs",
            "voice": "🎤・voice-logs",
            "server": "🖥️・server-logs",
            "thread": "🧵・thread-logs",
            "emoji": "😀・emoji-logs",
        }

        created_channels = {}

        # ==========================================
        # CREATE / REUSE CHANNELS
        # ==========================================

        for log_type, channel_name in log_channels.items():

            channel = discord.utils.get(
                category.channels,
                name=channel_name
            )

            if channel is None:

                channel = await guild.create_text_channel(
                    channel_name,
                    category=category,
                    reason="Iris logging setup"
                )

            created_channels[log_type] = channel.id

        # ==========================================
        # SAVE TO MONGODB
        # ==========================================

        await set_all_log_channels(
            guild.id,
            created_channels
        )

        # ==========================================
        # RESPONSE
        # ==========================================

        embed = IrisEmbed.success(
            "📜 Logging Setup Complete",
            "All Iris logging channels have been created and configured."
        )

        for log_type, channel_name in log_channels.items():

            channel = guild.get_channel(
                created_channels[log_type]
            )

            if channel:
                embed.add_field(
                    name=log_type.title(),
                    value=channel.mention,
                    inline=True
                )

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(LoggingCore(bot))