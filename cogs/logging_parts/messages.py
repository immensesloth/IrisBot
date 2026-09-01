import discord
from discord.ext import commands

from utils.embeds import IrisEmbed
from database.models import get_log_channel


class MessageLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("🔥 MessageLogging COG INITIALIZED")

    # ==========================================
    # MESSAGE DELETE
    # ==========================================

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        print("🔥🔥 RAW DELETE LISTENER FIRED 🔥🔥")
        print("Message ID:", payload.message_id)
        print("Channel ID:", payload.channel_id)
        print("Guild ID:", payload.guild_id)

        # Ignore DMs
        if payload.guild_id is None:
            print("DM - ignored")
            return

        # Get message log channel
        channel_id = await get_log_channel(
            payload.guild_id,
            "message"
        )

        print(
            "💬 MESSAGE LOG CHANNEL ID:",
            channel_id
        )

        if not channel_id:
            print("❌ NO MESSAGE LOG CHANNEL")
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        print(
            "💬 MESSAGE LOG CHANNEL:",
            log_channel
        )

        if log_channel is None:
            print("❌ MESSAGE LOG CHANNEL NOT FOUND")
            return

        # Try to get cached message information
        message = payload.cached_message

        if message is not None:

            if message.author.bot:
                print("Bot message - ignored")
                return

            content = (
                message.content
                if message.content
                else "*No text content*"
            )

            author = message.author.mention
            channel = message.channel.mention

        else:

            print("⚠️ Message was not cached")

            content = "*Message content unavailable*"
            author = "*Unknown*"

            source_channel = self.bot.get_channel(
                payload.channel_id
            )

            channel = (
                source_channel.mention
                if source_channel
                else f"`{payload.channel_id}`"
            )

        embed = IrisEmbed.error(
            "🗑️ Message Deleted",
            content
        )

        embed.add_field(
            name="Author",
            value=author,
            inline=True
        )

        embed.add_field(
            name="Channel",
            value=channel,
            inline=True
        )

        embed.add_field(
            name="Message ID",
            value=str(payload.message_id),
            inline=False
        )

        await log_channel.send(
            embed=embed
        )

        print("✅ MESSAGE DELETE LOG SENT")

    # ==========================================
    # MESSAGE EDIT
    # ==========================================

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before,
        after
    ):

        print("✏️ MESSAGE EDIT EVENT FIRED")

        if before.author.bot:
            print("Bot message - ignored")
            return

        if not before.guild:
            print("DM - ignored")
            return

        print("Before:", before.content)
        print("After:", after.content)

        if before.content == after.content:
            print("Content did not change")
            return

        channel_id = await get_log_channel(
            before.guild.id,
            "message"
        )

        print(
            "💬 MESSAGE EDIT LOG CHANNEL ID:",
            channel_id
        )

        if not channel_id:
            print("❌ NO MESSAGE LOG CHANNEL")
            return

        log_channel = self.bot.get_channel(
            channel_id
        )

        print(
            "💬 MESSAGE EDIT LOG CHANNEL:",
            log_channel
        )

        if log_channel is None:
            print("❌ MESSAGE LOG CHANNEL NOT FOUND")
            return

        embed = IrisEmbed.warning(
            "✏️ Message Edited",
            f"[Jump to message]({after.jump_url})"
        )

        embed.add_field(
            name="Author",
            value=before.author.mention,
            inline=True
        )

        embed.add_field(
            name="Channel",
            value=before.channel.mention,
            inline=True
        )

        embed.add_field(
            name="Before",
            value=(
                before.content[:1024]
                if before.content
                else "*No text content*"
            ),
            inline=False
        )

        embed.add_field(
            name="After",
            value=(
                after.content[:1024]
                if after.content
                else "*No text content*"
            ),
            inline=False
        )

        await log_channel.send(
            embed=embed
        )

        print("✅ MESSAGE EDIT LOG SENT")


async def setup(bot):
    cog = MessageLogging(bot)

    await bot.add_cog(cog)

    bot.add_listener(
        cog.on_raw_message_delete,
        "on_raw_message_delete"
    )

    print("🔥 RAW DELETE LISTENER MANUALLY REGISTERED")