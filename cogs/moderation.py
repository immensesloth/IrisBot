import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta

from utils.embeds import IrisEmbed
from database.models import (
    add_warning,
    get_warnings,
    clear_warnings,
    get_log_channel
)


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ==========================================
    # BAN
    # ==========================================

    @app_commands.command(
        name="ban",
        description="Ban a member."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):

        if member == interaction.user:
            return await interaction.response.send_message(
                "❌ You can't ban yourself.",
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ That member has an equal or higher role.",
                ephemeral=True
            )

        if member.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ My role is too low.",
                ephemeral=True
            )

        await member.ban(reason=reason)
            
        # ==========================================
        # LOG BAN
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
        )

        if log_channel:
            log_embed = IrisEmbed.error(
                "🔨 Member Banned",
                f"{member.mention} has been banned."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.error(
            "🔨 Member Banned",
            f"{member.mention} has been banned."
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # KICK
    # ==========================================

    @app_commands.command(
        name="kick",
        description="Kick a member."
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided"
    ):

        if member == interaction.user:
            return await interaction.response.send_message(
                "❌ You can't kick yourself.",
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ That member has an equal or higher role.",
                ephemeral=True
            )

        if member.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ My role is too low.",
                ephemeral=True
            )

        await member.kick(reason=reason)

        # ==========================================
        # LOG KICK
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.warning(
                "👢 Member Kicked",
                f"{member.mention} has been kicked."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.warning(
            "👢 Member Kicked",
            f"{member.mention} has been kicked."
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # TIMEOUT
    # ==========================================

    @app_commands.command(
        name="timeout",
        description="Timeout a member."
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: app_commands.Range[int, 1, 10080],
        reason: str = "No reason provided"
    ):

        if member == interaction.user:
            return await interaction.response.send_message(
                "❌ You can't timeout yourself.",
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ That member has an equal or higher role.",
                ephemeral=True
            )

        if member.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ My role is too low.",
                ephemeral=True
            )

        await member.timeout(
            timedelta(minutes=minutes),
            reason=reason
        )

        # ==========================================
        # LOG TIMEOUT
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.warning(
                "⏳ Member Timed Out",
                f"{member.mention} has been timed out."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Duration",
                value=f"{minutes} minute(s)",
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.warning(
            "⏳ Member Timed Out",
            f"{member.mention} has been timed out."
        )

        embed.add_field(
            name="Duration",
            value=f"{minutes} minute(s)",
            inline=True
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # WARN
    # ==========================================

    @app_commands.command(
        name="warn",
        description="Warn a member."
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str
    ):

        if member.bot:
            return await interaction.response.send_message(
                "❌ You cannot warn bots.",
                ephemeral=True
            )

        await add_warning(
            interaction.guild.id,
            member.id,
            interaction.user.id,
            reason
        )

        # ==========================================
        # LOG WARN
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
        )

        if log_channel:
            log_embed = IrisEmbed.warning(
                "⚠️ Member Warned",
                f"{member.mention} has been warned."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.warning(
            "⚠️ Member Warned",
            f"{member.mention} has been warned."
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # WARNINGS
    # ==========================================

    @app_commands.command(
        name="warnings",
        description="Show a member's warnings."
    )
    async def warnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        data = await get_warnings(
            interaction.guild.id,
            member.id
        )

        if not data:
            embed = IrisEmbed.default(
                "Warnings",
                f"{member.mention} has no warnings."
            )

            return await interaction.response.send_message(embed=embed)

        embed = IrisEmbed.default(
            f"Warnings for {member}"
        )

        for index, warning in enumerate(data, start=1):

            embed.add_field(
                name=f"Warning {index}",
                value=warning["reason"],
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # CLEAR WARNINGS
    # ==========================================

    @app_commands.command(
        name="clearwarnings",
        description="Clear all warnings for a member."
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def clearwarnings(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        await clear_warnings(
            interaction.guild.id,
            member.id
        )

        # ==========================================
        # LOG CLEAR WARNINGS
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        log_channel = None

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.warning(
                "🧹 Warnings Cleared",
                f"All warnings for {member.mention} have been cleared."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.success(
            "Warnings Cleared",
            f"All warnings for {member.mention} have been removed."
        )

        await interaction.response.send_message(
            embed=embed
        )


    # ==========================================
    # PURGE
    # ==========================================

    @app_commands.command(
        name="purge",
        description="Delete multiple messages."
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100]
    ):

        await interaction.response.defer(ephemeral=True)

        deleted = await interaction.channel.purge(limit=amount)

        # ==========================================
        # LOG PURGE
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.success(
                "🧹 Messages Purged",
                f"**{len(deleted)}** messages were deleted."
            )

            log_embed.add_field(
                name="Channel",
                value=interaction.channel.mention,
                inline=True
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.success(
            "🗑️ Messages Deleted",
            f"Successfully deleted **{len(deleted)}** messages."
        )

        await interaction.followup.send(
        embed=embed,
        ephemeral=True
        ) 

    # ==========================================
    # LOCK
    # ==========================================

    @app_commands.command(
        name="lock",
        description="Lock the current channel."
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def lock(
        self,
        interaction: discord.Interaction,
        reason: str = "No reason provided"
   ):

        overwrite = interaction.channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason=reason
        )

        # ==========================================
        # LOG CHANNEL LOCK
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "channel"
        )

        log_channel = None

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.warning(
                "🔒 Channel Locked",
                f"{interaction.channel.mention} was locked."
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.success(
            "🔒 Channel Locked",
            f"{interaction.channel.mention} has been locked."
       )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=True
       )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # UNLOCK
    # ==========================================

    @app_commands.command(
        name="unlock",
        description="Unlock the current channel."
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def unlock(
        self,
        interaction: discord.Interaction,
        reason: str = "No reason provided" 
    ):
        overwrite = interaction.channel.overwrites_for(
            interaction.guild.default_role
    )

        overwrite.send_messages = None

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
            reason=reason
        )

        # ==========================================
        # LOG CHANNEL UNLOCK
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "channel"
        )

        log_channel = None

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.success(
                "🔓 Channel Unlocked",
                f"{interaction.channel.mention} was unlocked."
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            log_embed.add_field(
                name="Reason",
                value=reason,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.success(
        "🔓 Channel Unlocked",
        f"{interaction.channel.mention} has been unlocked."
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=True
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # SLOWMODE
    # ==========================================

    @app_commands.command(
        name="slowmode",
        description="Set the slowmode for the current channel."
    )
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slowmode(
        self,
        interaction: discord.Interaction,
        seconds: app_commands.Range[int, 0, 21600]
   ):
        await interaction.channel.edit(
            slowmode_delay=seconds
        )

        # ==========================================
        # LOG SLOWMODE
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "channel"
        )

        log_channel = None

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            if seconds == 0:
                log_embed = IrisEmbed.success(
                    "🐌 Slowmode Disabled",
                    f"Slowmode was disabled in {interaction.channel.mention}."
                )
            else:
                log_embed = IrisEmbed.warning(
                    "🐌 Slowmode Updated",
                    f"Slowmode set to **{seconds} seconds** in {interaction.channel.mention}."
                )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        if seconds == 0:
            embed = IrisEmbed.success(
                "🐌 Slowmode Disabled",
                f"Slowmode has been disabled in {interaction.channel.mention}."
           )
        else:
            embed = IrisEmbed.success(
                "🐌 Slowmode Enabled",
                f"Slowmode has been set to **{seconds} seconds** in {interaction.channel.mention}."
            )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
       )

        await interaction.response.send_message(embed=embed)    

    # ==========================================
    # NICKNAME
    # ==========================================

    @app_commands.command(
        name="nickname",
        description="Change a member's nickname."
    )
    @app_commands.checks.has_permissions(manage_nicknames=True)
    async def nickname(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        nickname: str
    ):

        if member == interaction.user:
            return await interaction.response.send_message(
                "❌ You cannot change your own nickname using this command.",
                ephemeral=True
            )

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ That member has an equal or higher role than you.",
                ephemeral=True
            )

        if member.top_role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ My role is too low to change that member's nickname.",
                ephemeral=True
            )

        await member.edit(nick=nickname)

                # ==========================================
        # LOG NICKNAME CHANGE
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "member"
        )

        log_channel = None

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

        if log_channel:
            log_embed = IrisEmbed.success(
                "📝 Nickname Changed",
                f"{member.mention}'s nickname was changed."
            )

            log_embed.add_field(
                name="User",
                value=f"{member} (`{member.id}`)",
                inline=False
            )

            log_embed.add_field(
                name="New Nickname",
                value=nickname,
                inline=True
            )

            log_embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            await log_channel.send(
                embed=log_embed
            )

        embed = IrisEmbed.success(
            "📝 Nickname Changed",
            f"{member.mention}'s nickname has been updated."
        )

        embed.add_field(
            name="New Nickname",
            value=nickname,
            inline=False
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    # ==========================================
    # ROLE
    # ==========================================

    @app_commands.command(
        name="role",
        description="Add or remove a role from a member."
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        role: discord.Role
    ):

        if role >= interaction.guild.me.top_role:
            return await interaction.response.send_message(
                "❌ My role is lower than that role.",
                ephemeral=True
            )

        if role >= interaction.user.top_role:
            return await interaction.response.send_message(
                "❌ You cannot manage a role equal to or higher than your highest role.",
                ephemeral=True
            )

        if role in member.roles:
            await member.remove_roles(role)

            action = "Role Removed"
            description = f"Removed {role.mention} from {member.mention}."
            log_type = "warning"

        else:
            await member.add_roles(role)

            action = "Role Added"
            description = f"Added {role.mention} to {member.mention}."
            log_type = "success"

        # ==========================================
        # LOG ROLE ACTION
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

            if log_channel:
                if log_type == "warning":
                    log_embed = IrisEmbed.warning(
                        f"🎭 {action}",
                        description
                    )
                else:
                    log_embed = IrisEmbed.success(
                        f"🎭 {action}",
                        description
                    )

                log_embed.add_field(
                    name="User",
                    value=f"{member} (`{member.id}`)",
                    inline=False
                )

                log_embed.add_field(
                    name="Role",
                    value=f"{role.mention} (`{role.id}`)",
                    inline=True
                )

                log_embed.add_field(
                    name="Moderator",
                    value=interaction.user.mention,
                    inline=True
                )

                await log_channel.send(
                    embed=log_embed
                )

        # ==========================================
        # RESPONSE
        # ==========================================

        embed = (
            IrisEmbed.warning(
                "➖ Role Removed",
                f"Removed {role.mention} from {member.mention}."
            )
            if log_type == "warning"
            else IrisEmbed.success(
                "➕ Role Added",
                f"Added {role.mention} to {member.mention}."
            )
        )

        embed.add_field(
            name="Moderator",
            value=interaction.user.mention,
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # UNBAN
    # ==========================================

    @app_commands.command(
        name="unban",
        description="Unban a user from the server."
    )

    @app_commands.checks.has_permissions(ban_members=True)
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "No reason provided"
    ):

        # Make sure the ID is valid
        try:
            user_id_int = int(user_id)
        except ValueError:
            return await interaction.response.send_message(
                "❌ Invalid user ID. Please enter a valid Discord user ID.",
                ephemeral=True
            )

        # Check if the user is actually banned
        try:
            banned_user = await interaction.guild.fetch_ban(
                discord.Object(id=user_id_int)
           )

        except discord.NotFound:
            return await interaction.response.send_message(
                "❌ That user is not banned.",
                ephemeral=True
            )

        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ I don't have permission to view the ban list.",
                ephemeral=True
            )

        # Get actual user information
        user = banned_user.user

        # Unban
        try:
            await interaction.guild.unban(
                user,
                reason=reason
            )

        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ I don't have permission to unban this user.",
                ephemeral=True
            )

        except discord.HTTPException as e:
            return await interaction.response.send_message(
                f"❌ Failed to unban the user.\n`{e}`",
                ephemeral=True
            )

        # ==========================================
        # LOG UNBAN
        # ==========================================

        log_channel_id = await get_log_channel(
            interaction.guild.id,
            "mod"
        )

        if log_channel_id:
            log_channel = self.bot.get_channel(
                log_channel_id
            )

            if log_channel:
                log_embed = IrisEmbed.success(
                    "🔓 Member Unbanned",
                    f"**{user}** has been unbanned."
                )

                log_embed.add_field(
                    name="User",
                    value=f"{user} (`{user.id}`)",
                    inline=False
                )

                log_embed.add_field(
                    name="Moderator",
                    value=interaction.user.mention,
                    inline=True
                )

                log_embed.add_field(
                    name="Reason",
                    value=reason,
                    inline=False
                )

                await log_channel.send(
                    embed=log_embed
                )

            # ==========================================
            # COMMAND RESPONSE
            # ==========================================

            embed = IrisEmbed.success(
                "🔓 Member Unbanned",
                f"{user.mention} has been unbanned."
            )

            embed.add_field(
                name="Moderator",
                value=interaction.user.mention,
                inline=True
            )

            embed.add_field(
                name="Reason",
                value=reason,
                inline=False
            )

            await interaction.response.send_message(
            embed=embed
            )

    # ==========================================
    # ERROR HANDLER
    # ==========================================

    @ban.error
    @kick.error
    @timeout.error
    @warn.error
    @warnings.error
    @clearwarnings.error
    @purge.error
    @lock.error
    @unlock.error
    @slowmode.error
    @nickname.error
    @role.error
    @unban.error
    async def moderation_error(
        self,
        interaction: discord.Interaction,
        error
    ):

        if isinstance(error, app_commands.MissingPermissions):

            embed = IrisEmbed.error(
                "Permission Denied",
                "You don't have permission to use this command."
            )

            await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Moderation(bot))