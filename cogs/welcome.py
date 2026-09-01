import discord
from discord.ext import commands
from discord import app_commands

from database.models import (
    set_welcome_channel,
    get_welcome_settings,
    remove_welcome,
    set_goodbye_channel,
    get_goodbye_settings,
    remove_goodbye
)

from utils.embeds import IrisEmbed


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("🔥 Welcome COG INITIALIZED")

    # ==========================================
    # SET WELCOME
    # ==========================================

    @app_commands.command(
        name="setwelcome",
        description="Configure the welcome message and its server channels."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        rules: discord.TextChannel | None = None,
        roles: discord.TextChannel | None = None,
        chat: discord.TextChannel | None = None
    ):

        await set_welcome_channel(
            interaction.guild.id,
            channel.id,
            rules.id if rules else None,
            roles.id if roles else None,
            chat.id if chat else None
        )

        embed = IrisEmbed.success(
            "🌸 Welcome System Enabled",
            (
                f"Welcome messages will now be sent in "
                f"{channel.mention}."
            )
        )

        embed.add_field(
            name="📋 System",
            value="Member Welcome Messages",
            inline=True
        )

        embed.add_field(
            name="📍 Welcome Channel",
            value=channel.mention,
            inline=True
        )

        configured = []
        if rules:
            configured.append(f"📜 Rules: {rules.mention}")
        if roles:
            configured.append(f"🎭 Roles: {roles.mention}")
        if chat:
            configured.append(f"💬 Chat: {chat.mention}")

        embed.add_field(
            name="🔗 Server Channels",
            value="\n".join(configured) if configured else "Not configured — you can add them with `/setwelcome`.",
            inline=False
        )

        embed.set_footer(
            text="Iris • Welcome System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # REMOVE WELCOME
    # ==========================================

    @app_commands.command(
        name="removewelcome",
        description="Disable the welcome system."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def removewelcome(
        self,
        interaction: discord.Interaction
    ):

        await remove_welcome(
            interaction.guild.id
        )

        embed = IrisEmbed.warning(
            "🌸 Welcome System Disabled",
            "Welcome messages have been disabled."
        )

        embed.set_footer(
            text="Iris • Welcome System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # SET GOODBYE
    # ==========================================

    @app_commands.command(
        name="setgoodbye",
        description="Set the channel where goodbye messages are sent."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setgoodbye(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        await set_goodbye_channel(
            interaction.guild.id,
            channel.id
        )

        embed = IrisEmbed.success(
            "🚪 Goodbye System Enabled",
            (
                f"Goodbye messages will now be sent in "
                f"{channel.mention}."
            )
        )

        embed.add_field(
            name="📋 System",
            value="Member Goodbye Messages",
            inline=True
        )

        embed.add_field(
            name="📍 Channel",
            value=channel.mention,
            inline=True
        )

        embed.set_footer(
            text="Iris • Goodbye System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # REMOVE GOODBYE
    # ==========================================

    @app_commands.command(
        name="removegoodbye",
        description="Disable the goodbye system."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def removegoodbye(
        self,
        interaction: discord.Interaction
    ):

        await remove_goodbye(
            interaction.guild.id
        )

        embed = IrisEmbed.warning(
            "🚪 Goodbye System Disabled",
            "Goodbye messages have been disabled."
        )

        embed.set_footer(
            text="Iris • Goodbye System"
        )

        await interaction.response.send_message(
            embed=embed
        )

    # ==========================================
    # MEMBER JOIN
    # ==========================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        member: discord.Member
    ):

        config = await get_welcome_settings(
            member.guild.id
        )

        if not config:
            return

        if not config.get("enabled"):
            return

        channel_id = config.get("channel_id")

        if not channel_id:
            return

        welcome_channel = self.bot.get_channel(
            channel_id
        )

        if welcome_channel is None:
            return

        # ------------------------------------------
        # SERVER-SPECIFIC CHANNELS
        # ------------------------------------------

        rules_channel = None
        roles_channel = None
        general_channel = None

        rules_channel_id = config.get("rules_channel_id")
        roles_channel_id = config.get("roles_channel_id")
        general_channel_id = config.get("general_channel_id")

        if rules_channel_id:
            rules_channel = member.guild.get_channel(rules_channel_id)

        if roles_channel_id:
            roles_channel = member.guild.get_channel(roles_channel_id)

        if general_channel_id:
            general_channel = member.guild.get_channel(general_channel_id)

        # ------------------------------------------
        # WELCOME EMBED
        # ------------------------------------------

        embed = IrisEmbed.success(
            "🌸 Welcome to Iris!",
            (
                f"Hey {member.mention}! 👋\n\n"
                "We're genuinely happy to have you here. 💗\n\n"
                f"You're our **#{member.guild.member_count} "
                "member**!\n"
                "Take a moment to get settled, explore the "
                "server, and meet the community."
            )
        )

        # ------------------------------------------
        # MEMBER AVATAR
        # ------------------------------------------

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        # ------------------------------------------
        # RULES
        # ------------------------------------------

        if rules_channel:
            embed.add_field(
                name="📜 Read the Rules",
                value=(
                    "Before you start chatting, make sure you've "
                    "read our server rules.\n\n"
                    f"📖 Head over to {rules_channel.mention}"
                ),
                inline=False
            )

        # ------------------------------------------
        # SELF ROLES
        # ------------------------------------------

        if roles_channel:
            embed.add_field(
                name="🎭 Choose Your Roles",
                value=(
                    "Customize your experience by choosing the "
                    "roles that suit you.\n\n"
                    f"🎨 Pick your roles in {roles_channel.mention}"
                ),
                inline=False
            )

        # ------------------------------------------
        # GENERAL CHAT
        # ------------------------------------------

        if general_channel:
            embed.add_field(
                name="💬 Meet the Community",
                value=(
                    "Don't be shy! Say hello, introduce yourself, "
                    "and jump into the conversation.\n\n"
                    f"💬 Start chatting in {general_channel.mention}"
                ),
                inline=False
            )

        # ------------------------------------------
        # SERVER MESSAGE
        # ------------------------------------------

        embed.add_field(
            name="💖 A Little Reminder",
            value=(
                "Be respectful • Have fun • Make friends\n"
                "Let's keep Iris a welcoming place for everyone."
            ),
            inline=False
        )

        # ------------------------------------------
        # FOOTER
        # ------------------------------------------

        embed.set_footer(
            text="Iris • We're glad you're here!"
        )

        embed.timestamp = discord.utils.utcnow()

        await welcome_channel.send(
            embed=embed
        )

    # ==========================================
    # MEMBER LEAVE
    # ==========================================

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        member: discord.Member
    ):

        config = await get_goodbye_settings(
            member.guild.id
        )

        if not config:
            return

        if not config.get("enabled"):
            return

        channel_id = config.get("channel_id")

        if not channel_id:
            return

        goodbye_channel = self.bot.get_channel(
            channel_id
        )

        if goodbye_channel is None:
            return

        # ------------------------------------------
        # GOODBYE EMBED
        # ------------------------------------------

        embed = IrisEmbed.warning(
            "👋 We'll Miss You!",
            (
                f"**{member}** has left **Iris**.\n\n"
                "Thank you for being part of our community. 💗\n"
                "We hope you enjoyed your time with us and "
                "wish you nothing but the best!"
            )
        )

        # ------------------------------------------
        # MEMBER AVATAR
        # ------------------------------------------

        embed.set_thumbnail(
            url=member.display_avatar.url
        )

        # ------------------------------------------
        # MEMBER INFO
        # ------------------------------------------

        embed.add_field(
            name="👤 Member",
            value=(
                f"{member.mention}\n"
                f"`{member}`"
            ),
            inline=True
        )

        embed.add_field(
            name="👥 Members Remaining",
            value=str(
                member.guild.member_count
            ),
            inline=True
        )

        # ------------------------------------------
        # GOODBYE MESSAGE
        # ------------------------------------------

        embed.add_field(
            name="🌸 Until We Meet Again",
            value=(
                "Once a part of Iris, "
                "always a part of our memories. 💖\n\n"
                "Take care and stay safe!"
            ),
            inline=False
        )

        # ------------------------------------------
        # FOOTER
        # ------------------------------------------

        embed.set_footer(
            text="Iris • Until we meet again!"
        )

        embed.timestamp = discord.utils.utcnow()

        await goodbye_channel.send(
            embed=embed
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):
    await bot.add_cog(Welcome(bot))
    print("✅ Welcome COG LOADED")
