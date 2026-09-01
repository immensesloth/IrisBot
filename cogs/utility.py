import discord
from discord.ext import commands
from discord import app_commands

from utils.embeds import IrisEmbed


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("🔥 Utility COG INITIALIZED")

    # ==========================================
    # SERVER INFO
    # ==========================================

    @app_commands.command(
        name="serverinfo",
        description="Show information about the server."
    )
    async def serverinfo(
        self,
        interaction: discord.Interaction
    ):

        guild = interaction.guild

        embed = IrisEmbed.success(
            f"🖥️ {guild.name}",
            "Server Information"
        )

        if guild.icon:
            embed.set_thumbnail(
                url=guild.icon.url
            )

        embed.add_field(
            name="👑 Owner",
            value=f"<@{guild.owner_id}>",
            inline=True
        )

        embed.add_field(
            name="👥 Members",
            value=str(guild.member_count),
            inline=True
        )

        embed.add_field(
            name="📁 Channels",
            value=str(len(guild.channels)),
            inline=True
        )

        embed.add_field(
            name="💬 Text Channels",
            value=str(len(guild.text_channels)),
            inline=True
        )

        embed.add_field(
            name="🔊 Voice Channels",
            value=str(len(guild.voice_channels)),
            inline=True
        )

        embed.add_field(
            name="🎭 Roles",
            value=str(len(guild.roles)),
            inline=True
        )

        embed.add_field(
            name="🆔 Server ID",
            value=str(guild.id),
            inline=True
        )

        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=False
        )

        embed.add_field(
            name="🚀 Boost Level",
            value=str(guild.premium_tier),
            inline=True
        )

        embed.add_field(
            name="💎 Boosts",
            value=str(guild.premium_subscription_count),
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # USER INFO
    # ==========================================

    @app_commands.command(
        name="userinfo",
        description="Show information about a user."
    )
    @app_commands.describe(
        member="The user to inspect."
    )
    async def userinfo(
        self,
        interaction: discord.Interaction,
        member: discord.Member
    ):

        embed = IrisEmbed.success(
            f"👤 {member}",
            "User Information"
        )

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        embed.add_field(
            name="🆔 User ID",
            value=str(member.id),
            inline=True
        )

        embed.add_field(
            name="🤖 Bot",
            value="Yes" if member.bot else "No",
            inline=True
        )

        embed.add_field(
            name="📅 Account Created",
            value=f"<t:{int(member.created_at.timestamp())}:F>",
            inline=False
        )

        embed.add_field(
            name="📥 Joined Server",
            value=(
                f"<t:{int(member.joined_at.timestamp())}:F>"
                if member.joined_at
                else "Unknown"
            ),
            inline=False
        )

        roles = [
            role.mention
            for role in member.roles
            if role != interaction.guild.default_role
        ]

        embed.add_field(
            name="🎭 Roles",
            value=(
                " ".join(roles)
                if roles
                else "No roles"
            ),
            inline=False
        )

        embed.add_field(
            name="🏷️ Nickname",
            value=member.nick or "None",
            inline=True
        )

        embed.add_field(
            name="🎨 Display Name",
            value=member.display_name,
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # ROLE INFO
    # ==========================================

    @app_commands.command(
        name="roleinfo",
        description="Show information about a role."
    )
    @app_commands.describe(
        role="The role to inspect."
    )
    async def roleinfo(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        embed = IrisEmbed.success(
            f"🎭 {role.name}",
            "Role Information"
        )

        embed.add_field(
            name="🆔 Role ID",
            value=str(role.id),
            inline=True
        )

        embed.add_field(
            name="📌 Position",
            value=str(role.position),
            inline=True
        )

        embed.add_field(
            name="👥 Members",
            value=str(len(role.members)),
            inline=True
        )

        embed.add_field(
            name="🎨 Color",
            value=str(role.color),
            inline=True
        )

        embed.add_field(
            name="📢 Mentionable",
            value="Yes" if role.mentionable else "No",
            inline=True
        )

        embed.add_field(
            name="🤖 Managed",
            value="Yes" if role.managed else "No",
            inline=True
        )

        embed.add_field(
            name="📍 Displayed Separately",
            value="Yes" if role.hoist else "No",
            inline=True
        )

        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(role.created_at.timestamp())}:F>",
            inline=False
        )

        permissions = []

        permission_names = {
            "administrator": "Administrator",
            "manage_guild": "Manage Server",
            "manage_channels": "Manage Channels",
            "manage_roles": "Manage Roles",
            "manage_messages": "Manage Messages",
            "kick_members": "Kick Members",
            "ban_members": "Ban Members",
            "moderate_members": "Moderate Members",
            "manage_nicknames": "Manage Nicknames",
            "mention_everyone": "Mention Everyone",
            "view_audit_log": "View Audit Log"
        }

        for permission, name in permission_names.items():
            if getattr(role.permissions, permission, False):
                permissions.append(name)

        embed.add_field(
            name="🔐 Key Permissions",
            value=(
                ", ".join(permissions)
                if permissions
                else "No special permissions"
            ),
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # CHANNEL INFO
    # ==========================================

    @app_commands.command(
        name="channelinfo",
        description="Show information about a channel."
    )
    @app_commands.describe(
        channel="The channel to inspect."
    )
    async def channelinfo(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel
    ):

        embed = IrisEmbed.success(
            f"📁 {channel.name}",
            "Channel Information"
        )

        embed.add_field(
            name="🆔 Channel ID",
            value=str(channel.id),
            inline=True
        )

        embed.add_field(
            name="📝 Type",
            value=str(channel.type).title(),
            inline=True
        )

        embed.add_field(
            name="📂 Category",
            value=(
                channel.category.mention
                if channel.category
                else "No Category"
            ),
            inline=True
        )

        embed.add_field(
            name="📅 Created",
            value=f"<t:{int(channel.created_at.timestamp())}:F>",
            inline=False
        )

        # Text / forum channels
        if isinstance(
            channel,
            (
                discord.TextChannel,
                discord.Thread,
                discord.ForumChannel
            )
        ):
            slowmode = getattr(
                channel,
                "slowmode_delay",
                0
            )

            embed.add_field(
                name="🐌 Slowmode",
                value=(
                    f"{slowmode} seconds"
                    if slowmode
                    else "Disabled"
                ),
                inline=True
            )

        # Text channel specific
        if isinstance(
            channel,
            discord.TextChannel
        ):
            embed.add_field(
                name="🧵 Threads",
                value=str(len(channel.threads)),
                inline=True
            )

        # Voice channel specific
        if isinstance(
            channel,
            discord.VoiceChannel
        ):
            embed.add_field(
                name="👥 User Limit",
                value=(
                    str(channel.user_limit)
                    if channel.user_limit
                    else "Unlimited"
                ),
                inline=True
            )

            embed.add_field(
                name="🔊 Bitrate",
                value=f"{channel.bitrate // 1000} kbps",
                inline=True
            )

        # Position
        embed.add_field(
            name="📌 Position",
            value=str(channel.position),
            inline=True
        )

        # Mention
        embed.add_field(
            name="🔗 Mention",
            value=channel.mention,
            inline=True
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # PING
    # ==========================================

    @app_commands.command(
        name="ping",
        description="Check the bot's latency."
    )
    async def ping(
        self,
        interaction: discord.Interaction
    ):

        latency = round(
            self.bot.latency * 1000
        )

        embed = IrisEmbed.success(
            "🏓 Pong!",
            f"Bot latency: **{latency}ms**"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # BOT INFO
    # ==========================================

    @app_commands.command(
        name="botinfo",
        description="Show information about the bot."
    )
    async def botinfo(
        self,
        interaction: discord.Interaction
    ):

        bot_user = self.bot.user

        embed = IrisEmbed.success(
            "🤖 Iris",
            "Bot Information"
        )

        if bot_user:
            embed.set_thumbnail(
                url=bot_user.display_avatar.url
            )

        embed.add_field(
            name="🤖 Bot",
            value=bot_user.mention if bot_user else "Unknown",
            inline=True
        )

        embed.add_field(
            name="🆔 Bot ID",
            value=str(bot_user.id) if bot_user else "Unknown",
            inline=True
        )

        embed.add_field(
            name="📡 Servers",
            value=str(len(self.bot.guilds)),
            inline=True
        )

        embed.add_field(
            name="👥 Users",
            value=str(len(self.bot.users)),
            inline=True
        )

        embed.add_field(
            name="⚡ Latency",
            value=f"{round(self.bot.latency * 1000)}ms",
            inline=True
        )

        embed.add_field(
            name="🧩 Commands",
            value=str(len(self.bot.tree.get_commands())),
            inline=True
        )

        if bot_user:
            embed.add_field(
                name="📅 Bot Account Created",
                value=f"<t:{int(bot_user.created_at.timestamp())}:F>",
                inline=False
            )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # UPTIME
    # ==========================================

    @app_commands.command(
        name="uptime",
        description="Show how long the bot has been online."
    )
    async def uptime(
        self,
        interaction: discord.Interaction
    ):

        if not hasattr(self.bot, "start_time"):
            return await interaction.response.send_message(
                "❌ Bot start time is not configured.",
                ephemeral=True
            )

        uptime = discord.utils.utcnow() - self.bot.start_time

        days = uptime.days
        hours, remainder = divmod(
            uptime.seconds,
            3600
        )
        minutes, seconds = divmod(
            remainder,
            60
        )

        parts = []

        if days:
            parts.append(f"{days}d")

        if hours:
            parts.append(f"{hours}h")

        if minutes:
            parts.append(f"{minutes}m")

        if seconds or not parts:
            parts.append(f"{seconds}s")

        uptime_text = " ".join(parts)

        embed = IrisEmbed.success(
            "⏱️ Iris Uptime",
            f"I've been online for **{uptime_text}**."
        )

        embed.add_field(
            name="🚀 Started",
            value=f"<t:{int(self.bot.start_time.timestamp())}:F>",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed
        )            

# ==========================================
# SETUP
# ==========================================

async def setup(bot):
    await bot.add_cog(Utility(bot))
    print("✅ Utility COG LOADED")