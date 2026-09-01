import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class EmojiStickerLogging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):

        channel_id = await get_log_channel(guild.id, "emoji")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        before_dict = {emoji.id: emoji for emoji in before}
        after_dict = {emoji.id: emoji for emoji in after}

        # CREATED
        for emoji_id, emoji in after_dict.items():
            if emoji_id not in before_dict:

                embed = IrisEmbed.success(
                    "😀 Emoji Created",
                    f"Emoji {emoji} was added to the server."
                )

                embed.add_field(
                    name="Emoji",
                    value=f"{emoji.name} (`{emoji.id}`)",
                    inline=False
                )

                await log_channel.send(embed=embed)

        # DELETED
        for emoji_id, emoji in before_dict.items():
            if emoji_id not in after_dict:

                embed = IrisEmbed.error(
                    "🗑️ Emoji Deleted",
                    f"Emoji **{emoji.name}** was removed."
                )

                embed.add_field(
                    name="Emoji",
                    value=f"{emoji.name} (`{emoji.id}`)",
                    inline=False
                )

                await log_channel.send(embed=embed)

        # UPDATED
        for emoji_id in before_dict.keys() & after_dict.keys():

            old = before_dict[emoji_id]
            new = after_dict[emoji_id]

            if old.name != new.name:

                embed = IrisEmbed.warning(
                    "✏️ Emoji Updated",
                    f"Emoji `{old.name}` was renamed to `{new.name}`."
                )

                embed.add_field(
                    name="Before",
                    value=old.name,
                    inline=True
                )

                embed.add_field(
                    name="After",
                    value=new.name,
                    inline=True
                )

                await log_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):

        channel_id = await get_log_channel(guild.id, "emoji")

        if not channel_id:
            return

        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        before_dict = {sticker.id: sticker for sticker in before}
        after_dict = {sticker.id: sticker for sticker in after}

        # CREATED
        for sticker_id, sticker in after_dict.items():
            if sticker_id not in before_dict:

                embed = IrisEmbed.success(
                    "🏷️ Sticker Created",
                    f"Sticker **{sticker.name}** was added."
                )

                embed.add_field(
                    name="Sticker",
                    value=f"{sticker.name} (`{sticker.id}`)",
                    inline=False
                )

                await log_channel.send(embed=embed)

        # DELETED
        for sticker_id, sticker in before_dict.items():
            if sticker_id not in after_dict:

                embed = IrisEmbed.error(
                    "🗑️ Sticker Deleted",
                    f"Sticker **{sticker.name}** was removed."
                )

                embed.add_field(
                    name="Sticker",
                    value=f"{sticker.name} (`{sticker.id}`)",
                    inline=False
                )

                await log_channel.send(embed=embed)

        # UPDATED
        for sticker_id in before_dict.keys() & after_dict.keys():

            old = before_dict[sticker_id]
            new = after_dict[sticker_id]

            if old.name != new.name:

                embed = IrisEmbed.warning(
                    "✏️ Sticker Updated",
                    f"Sticker `{old.name}` was renamed to `{new.name}`."
                )

                embed.add_field(
                    name="Before",
                    value=old.name,
                    inline=True
                )

                embed.add_field(
                    name="After",
                    value=new.name,
                    inline=True
                )

                await log_channel.send(embed=embed)                               
