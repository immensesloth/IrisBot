import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed
from database.models import (
    set_log_channel,
    get_log_channel,
    remove_log_channel
)


class Logging(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # SET LOG
    # ==========================================

    @app_commands.command(
        name="setlog",
        description="Set the logging channel."
    )
    @app_commands.checks.has_permissions(administrator=True)
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
    @app_commands.checks.has_permissions(administrator=True)
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

        channel = interaction.guild.get_channel(channel_id)

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
    @app_commands.checks.has_permissions(administrator=True)
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
    # MESSAGE DELETE
    # ==========================================

    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message: discord.Message
    ):

        # Ignore bot messages
        if message.author.bot:
            return

        # Ignore DMs
        if not message.guild:
            return

        # Get saved log channel
        channel_id = await get_log_channel(
            message.guild.id
        )

        if not channel_id:
            return

        # Find the log channel
        log_channel = self.bot.get_channel(channel_id)

        if log_channel is None:
            return

        # Create log embed
        embed = IrisEmbed.error(
            "🗑️ Message Deleted",
            message.content
            if message.content
            else "*No text content*"
        )

        embed.add_field(
            name="Author",
            value=message.author.mention,
            inline=True
        )

        embed.add_field(
            name="Channel",
            value=message.channel.mention,
            inline=True
        )

        # Send log
        await log_channel.send(
            embed=embed
        )

    # ==========================================
    # MESSAGE EDIT
    # ==========================================

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message
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

        channel_id = await get_log_channel(before.guild.id)
        print("Log channel ID:", channel_id)

        if not channel_id:
            print("No log channel configured")
            return

        log_channel = self.bot.get_channel(channel_id)
        print("Log channel object:", log_channel)

        if log_channel is None:
            print("Could not find log channel")
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
            value=before.content[:1024]
            if before.content
            else "*No text content*",
            inline=False
        )

        embed.add_field(
            name="After",
            value=after.content[:1024]
            if after.content
            else "*No text content*",
            inline=False
        )

        await log_channel.send(
            embed=embed
        )

    # ==========================================
    # MEMBER JOIN
    # ==========================================

    @commands.Cog.listener()
    async def on_member_join(self, member):

        # Get saved log channel
        channel_id = await get_log_channel(
            member.guild.id
        )

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

    # ==========================================
    # MEMBER LEAVE
    # ==========================================

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        # Get saved log channel
        channel_id = await get_log_channel(
            member.guild.id
        )

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

    # ==========================================
    # ROLE CREATED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):

        channel_id = await get_log_channel(
            role.guild.id
        )

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

    # ==========================================
    # ROLE DELETED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        channel_id = await get_log_channel(
            role.guild.id
        )

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

    # ==========================================
    # ROLE UPDATED
    # ==========================================

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

        channel_id = await get_log_channel(
            after.guild.id
        )

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

    # ==========================================
    # CHANNEL CREATED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):

        channel_id = await get_log_channel(
            channel.guild.id
        )

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

    # ==========================================
    # CHANNEL DELETED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        channel_id = await get_log_channel(
            channel.guild.id
        )

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

    # ==========================================
    # CHANNEL UPDATED
    # ==========================================

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

        channel_id = await get_log_channel(
            after.guild.id
        )

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

    # ==========================================
    # VOICE STATE UPDATE
    # ==========================================

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
        channel_id = await get_log_channel(
            member.guild.id
        )

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

    # ==========================================
    # SERVER / GUILD UPDATE
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):

        # Get log channel
        channel_id = await get_log_channel(
            after.id
        )

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

        # ==========================================
    # THREAD CREATED
    # ==========================================

    @commands.Cog.listener()
    async def on_thread_create(self, thread):

        channel_id = await get_log_channel(
            thread.guild.id
        )

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
    # ==========================================
    # THREAD DELETED
    # ==========================================

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):

        channel_id = await get_log_channel(
            thread.guild.id
        )

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

    # ==========================================
    # THREAD UPDATED
    # ==========================================

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):

        if (
            before.name == after.name
            and before.archived == after.archived
            and before.locked == after.locked
            and before.slowmode_delay == after.slowmode_delay
        ):
            return

        channel_id = await get_log_channel(
            after.guild.id
        )

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

        # ==========================================
    # EMOJI UPDATED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):

        channel_id = await get_log_channel(guild.id)

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

    # ==========================================
    # STICKER UPDATED
    # ==========================================

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild, before, after):

        channel_id = await get_log_channel(guild.id)

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

# ==========================================
# SETUP
# ==========================================

async def setup(bot):
    await bot.add_cog(Logging(bot))