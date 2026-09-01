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


# ==========================================
# IRIS CHANNELS
# ==========================================

RULES_CHANNEL_ID = 1272255305857892566
SELF_ROLE_CHANNEL_ID = 1269418461184917586
GENERAL_CHAT_CHANNEL_ID = 1270542333380788245


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        print("🔥 Welcome COG INITIALIZED")

    # ==========================================
    # SET WELCOME
    # ==========================================

    @app_commands.command(
        name="setwelcome",
        description="Set the channel where welcome messages are sent."
    )
    @app_commands.checks.has_permissions(manage_guild=True)
    async def setwelcome(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        await set_welcome_channel(
            interaction.guild.id,
            channel.id
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
            name="📍 Channel",
            value=channel.mention,
            inline=True
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
        # CHANNEL MENTIONS
        # ------------------------------------------

        rules_channel = member.guild.get_channel(
            RULES_CHANNEL_ID
        )

        self_role_channel = member.guild.get_channel(
            SELF_ROLE_CHANNEL_ID
        )

        general_channel = member.guild.get_channel(
            GENERAL_CHAT_CHANNEL_ID
        )

        rules_mention = (
            rules_channel.mention
            if rules_channel
            else f"<#{RULES_CHANNEL_ID}>"
        )

        self_role_mention = (
            self_role_channel.mention
            if self_role_channel
            else f"<#{SELF_ROLE_CHANNEL_ID}>"
        )

        general_mention = (
            general_channel.mention
            if general_channel
            else f"<#{GENERAL_CHAT_CHANNEL_ID}>"
        )

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

        embed.add_field(
            name="📜 Read the Rules",
            value=(
                "Before you start chatting, make sure you've "
                "read our server rules.\n\n"
                f"📖 Head over to {rules_mention}"
            ),
            inline=False
        )

        # ------------------------------------------
        # SELF ROLES
        # ------------------------------------------

        embed.add_field(
            name="🎭 Choose Your Roles",
            value=(
                "Customize your experience by choosing the "
                "roles that suit you.\n\n"
                f"🎨 Pick your roles in {self_role_mention}"
            ),
            inline=False
        )

        # ------------------------------------------
        # GENERAL CHAT
        # ------------------------------------------

        embed.add_field(
            name="💬 Meet the Community",
            value=(
                "Don't be shy! Say hello, introduce yourself, "
                "and jump into the conversation.\n\n"
                f"💬 Start chatting in {general_mention}"
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
