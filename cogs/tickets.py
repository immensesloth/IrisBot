import asyncio
import discord
import io
import html

from discord.ext import commands
from discord import app_commands
from pymongo import ReturnDocument

from database.database import settings
import database.database as database

from database.models import (
    set_ticket_settings,
    get_ticket_settings,
    create_ticket,
    get_ticket,
    get_user_open_ticket,
    close_ticket
)

from utils.embeds import IrisEmbed


# ==========================================
# TICKET NUMBER COUNTER
# ==========================================

async def get_next_ticket_number(guild_id):
    """
    Atomically get the next ticket number for this server.

    The counter is stored in the MongoDB settings document,
    so deleting tickets or restarting Iris does not reset it.
    """

    result = await settings.find_one_and_update(
        {"guild_id": guild_id},
        {"$inc": {"ticket_counter": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER
    )

    return int(result.get("ticket_counter", 1))


# ==========================================
# TICKET PANEL VIEW
# ==========================================

class TicketSetupView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        emoji="🎫",
        style=discord.ButtonStyle.primary,
        custom_id="iris:create_ticket"
    )
    async def create_ticket_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        config = await get_ticket_settings(
            interaction.guild.id
        )

        if not config or not config.get("enabled"):
            return await interaction.response.send_message(
                "❌ The ticket system is not configured.",
                ephemeral=True
            )

        # ==========================================
        # CHECK EXISTING TICKET
        # ==========================================

        existing_ticket = await get_user_open_ticket(
            interaction.guild.id,
            interaction.user.id
        )

        if existing_ticket:

            existing_channel = interaction.guild.get_channel(
                int(existing_ticket.get("channel_id"))
            )

            if existing_channel:

                return await interaction.response.send_message(
                    f"❌ You already have an open ticket: "
                    f"{existing_channel.mention}",
                    ephemeral=True
                )

        # ==========================================
        # CHOOSE TICKET CATEGORY
        # ==========================================

        await interaction.response.send_message(
            "📂 **Choose a category for your ticket:**",
            view=TicketCategoryView(config),
            ephemeral=True
        )


# ==========================================
# TICKET CATEGORY VIEW
# ==========================================

class TicketCategoryView(discord.ui.View):

    def __init__(self, config):
        super().__init__(timeout=120)
        self.config = config

    @discord.ui.select(
        placeholder="📂 Select a ticket category...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="General Support", value="general", emoji="🛠️", description="General questions and help"),
            discord.SelectOption(label="Bug Report", value="bug", emoji="🐛", description="Report a bug or technical problem"),
            discord.SelectOption(label="Report User", value="report", emoji="🚨", description="Report a user or rule violation"),
            discord.SelectOption(label="Purchase / Order", value="purchase", emoji="🛒", description="Questions about purchases or orders"),
            discord.SelectOption(label="Suggestion", value="suggestion", emoji="💡", description="Share an idea or suggestion"),
            discord.SelectOption(label="Partnership", value="partnership", emoji="🤝", description="Partnership or collaboration requests"),
            discord.SelectOption(label="Other", value="other", emoji="❓", description="Anything that doesn't fit the categories above")
        ]
    )
    async def category_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected = select.values[0]
        category_data = {
            "general": ("🛠️", "General Support", "support"),
            "bug": ("🐛", "Bug Report", "bug"),
            "report": ("🚨", "Report User", "report"),
            "purchase": ("🛒", "Purchase / Order", "purchase"),
            "suggestion": ("💡", "Suggestion", "suggestion"),
            "partnership": ("🤝", "Partnership", "partnership"),
            "other": ("❓", "Other", "other")
        }
        emoji, category_name, category_slug = category_data.get(selected, ("❓", "Other", "other"))
        await interaction.response.send_modal(
            TicketReasonModal(
                self.config,
                category_name=category_name,
                category_emoji=emoji,
                category_slug=category_slug
            )
        )


# ==========================================
# TICKET CREATION MODAL
# ==========================================

class TicketReasonModal(discord.ui.Modal):

    def __init__(self, config, category_name="Other", category_emoji="❓", category_slug="other"):
        super().__init__(title="Create Iris Ticket")
        self.config = config
        self.category_name = category_name
        self.category_emoji = category_emoji
        self.category_slug = category_slug

        self.name_input = discord.ui.TextInput(
            label="Your Name",
            placeholder="Enter your name...",
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=100
        )

        self.reason = discord.ui.TextInput(
            label="Reason",
            placeholder="Describe your question or issue...",
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=3,
            max_length=1000
        )

        self.add_item(self.name_input)
        self.add_item(self.reason)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user

        category = guild.get_channel(self.config.get("category_id"))
        support_role = guild.get_role(self.config.get("support_role_id"))

        if category is None:
            return await interaction.response.send_message(
                "❌ The configured ticket category no longer exists.", ephemeral=True
            )

        if support_role is None:
            return await interaction.response.send_message(
                "❌ The configured support role no longer exists.", ephemeral=True
            )

        existing_ticket = await get_user_open_ticket(guild.id, member.id)
        if existing_ticket:
            existing_channel = guild.get_channel(int(existing_ticket.get("channel_id")))
            if existing_channel:
                return await interaction.response.send_message(
                    f"❌ You already have an open ticket: {existing_channel.mention}",
                    ephemeral=True
                )

        ticket_number = await get_next_ticket_number(guild.id)
        display_name = str(self.name_input.value).strip()
        reason = str(self.reason.value).strip()

        safe_username = "".join(
            c for c in member.name.lower()
            if c.isalnum() or c == "-"
        )[:20] or "user"

        channel_name = f"{self.category_slug}-{ticket_number:04d}-{safe_username}"[:100]

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True, embed_links=True
            ),
            support_role: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, attach_files=True,
                embed_links=True, manage_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                view_channel=True, send_messages=True,
                read_message_history=True, manage_channels=True,
                manage_messages=True
            )
        }

        await interaction.response.defer(ephemeral=True)

        topic = (
            f"Iris Ticket | Number: {ticket_number} | "
            f"Category: {self.category_name} | Owner: {member.id} | "
            f"Name: {display_name} | Reason: {reason[:650]}"
        )[:1024]

        try:
            ticket_channel = await guild.create_text_channel(
                name=channel_name, category=category, overwrites=overwrites,
                topic=topic, reason=f"Iris Ticket created by {member}"
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ I don't have permission to create ticket channels.", ephemeral=True
            )
        except Exception as error:
            print(f"❌ Ticket channel creation error: {error}")
            return await interaction.followup.send(
                "❌ Something went wrong while creating your ticket.", ephemeral=True
            )

        try:
            await create_ticket(guild.id, ticket_channel.id, member.id, reason)
        except Exception as error:
            print(f"❌ Ticket database error: {error}")
            try:
                await ticket_channel.delete(reason="Iris Ticket database error")
            except Exception:
                pass
            return await interaction.followup.send(
                "❌ Your ticket could not be saved. Please try again.", ephemeral=True
            )

        embed = IrisEmbed.success(
            "🎫 Iris Ticket",
            (
                f"Welcome {member.mention}! 👋\n\n"
                "Thanks for contacting the **Iris Support Team**.\n\n"
                "📎 **Have an attachment?** Upload your screenshot, image, "
                "video, PDF, or other file directly in this ticket. Iris will "
                "automatically acknowledge it.\n\n"
                "🛡️ A support member will assist you as soon as possible."
            )
        )

        embed.add_field(name="👤 Name", value=display_name[:1024], inline=True)
        embed.add_field(name="🎫 Ticket Number", value=f"`#{ticket_number:04d}`", inline=True)
        embed.add_field(name=f"{self.category_emoji} Category", value=self.category_name, inline=True)
        embed.add_field(name="📝 Reason", value=reason[:1024], inline=False)
        embed.add_field(
            name="📎 Attachment",
            value="Upload your file below if you have one. It will be detected automatically.",
            inline=False
        )
        embed.add_field(
            name="📌 Important",
            value=(
                "Please don't spam or repeatedly ping the support team.\n"
                "Use **🔒 Close Ticket** when your issue has been resolved."
            ),
            inline=False
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        await ticket_channel.send(
            content=f"{member.mention} {support_role.mention}",
            embed=embed, view=TicketControlView()
        )

        await interaction.followup.send(
            f"🎫 Your Iris Ticket has been created: {ticket_channel.mention}",
            ephemeral=True
        )

        await send_ticket_log(
            guild, self.config, "🎫 Iris Ticket Created",
            (
                f"**Ticket:** `#{ticket_channel.name}`\n"
                f"**Ticket Number:** `#{ticket_number:04d}`\n"
                f"**User:** {member.mention}\n"
                f"**Name:** {display_name[:300]}\n"
                f"**Category:** {self.category_emoji} {self.category_name}\n"
                f"**Reason:** {reason[:700]}"
            ), success=True
        )


# ==========================================
# OPEN TICKET CONTROLS
# ==========================================

class TicketControlView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim Ticket",
        emoji="🎟️",
        style=discord.ButtonStyle.primary,
        custom_id="iris:claim_ticket"
    )
    async def claim_ticket_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(
            channel,
            discord.TextChannel
        ):
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        # Acknowledge immediately so a slow MongoDB connection cannot
        # make the Claim button appear frozen.
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception as error:
            print(f"❌ Failed to acknowledge claim interaction: {error}")
            return

        try:
            config = await asyncio.wait_for(
                get_ticket_settings(guild.id),
                timeout=3
            )
        except Exception as error:
            print(f"⚠️ Ticket settings lookup failed during claim: {error}")
            config = None

        support_role_id = (
            config.get("support_role_id")
            if config
            else None
        )

        # Fallback: the ticket channel already has the support role in its
        # permission overwrites, so claiming can still work if the DB is slow.
        if not support_role_id:
            try:
                for target, overwrite in channel.overwrites.items():
                    if (
                        isinstance(target, discord.Role)
                        and overwrite.view_channel is True
                        and overwrite.send_messages is True
                        and overwrite.manage_messages is True
                    ):
                        support_role_id = target.id
                        break
            except Exception:
                pass

        # ==========================================
        # CHECK SUPPORT ROLE
        # ==========================================

        is_support = (
            support_role_id
            and isinstance(
                interaction.user,
                discord.Member
            )
            and any(
                role.id == support_role_id
                for role in interaction.user.roles
            )
        )

        if not is_support:
            return await interaction.followup.send(
                "❌ Only the support team can claim tickets.",
                ephemeral=True
            )

        # ==========================================
        # CHECK IF ALREADY CLAIMED
        # ==========================================

        topic = channel.topic or ""

        if "Claimed By:" in topic:

            try:
                claimed_part = topic.split(
                    "Claimed By:",
                    1
                )[1]

                claimed_id = claimed_part.split(
                    "|",
                    1
                )[0].strip()

                claimed_user = guild.get_member(
                    int(claimed_id)
                )

                if claimed_user:
                    return await interaction.response.send_message(
                        f"❌ This ticket is already claimed by "
                        f"{claimed_user.mention}.",
                        ephemeral=True
                    )

            except Exception:
                pass

        # ==========================================
        # SAVE CLAIM IN CHANNEL TOPIC
        # ==========================================

        try:

            await channel.edit(
                topic=(
                    f"{topic} | "
                    f"Claimed By: {interaction.user.id} |"
                )[:1024],
                reason=(
                    f"Iris Ticket claimed by "
                    f"{interaction.user}"
                )
            )

        except Exception as error:

            print(
                f"⚠️ Could not update claim topic: {error}"
            )
            return await interaction.followup.send(
                "❌ I couldn't save the claim. Please try again.",
                ephemeral=True
            )

        # ==========================================
        # CHANGE BUTTON
        # ==========================================

        button.label = "Claimed"
        button.emoji = "✅"
        button.disabled = True

        try:

            await interaction.message.edit(
                view=self
            )

        except Exception:
            pass

        # ==========================================
        # CLAIM MESSAGE
        # ==========================================

        embed = IrisEmbed.success(
            "🎟️ Ticket Claimed",
            (
                f"This ticket has been claimed by "
                f"{interaction.user.mention}.\n\n"
                "They will be handling this ticket."
            )
        )

        embed.set_footer(
            text="Iris • Ticket System"
        )

        embed.timestamp = discord.utils.utcnow()

        await interaction.followup.send(
            embed=embed
        )

        # ==========================================
        # CLAIM LOG
        # ==========================================

        await send_ticket_log(
            guild,
            config,
            "🎟️ Iris Ticket Claimed",
            (
                f"**Ticket:** `#{channel.name}`\n"
                f"**Claimed By:** "
                f"{interaction.user.mention}"
            ),
            success=True
        )    

    @discord.ui.button(
        label="Close Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.secondary,
        custom_id="iris:close_ticket"
    )
    async def close_ticket_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(CloseTicketReasonModal())


# ==========================================
# CLOSE TICKET REASON MODAL
# ==========================================

class CloseTicketReasonModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Close Iris Ticket")

        self.close_reason = discord.ui.TextInput(
            label="Why are you closing this ticket?",
            placeholder="Example: Issue resolved, question answered, duplicate ticket...",
            style=discord.TextStyle.paragraph,
            required=True,
            min_length=2,
            max_length=500
        )

        self.add_item(self.close_reason)

    async def on_submit(self, interaction: discord.Interaction):
        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        # Acknowledge the button interaction immediately.
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception as error:
            print(f"❌ Failed to acknowledge close interaction: {error}")
            return

        try:
            # ==========================================
            # GET CONFIG
            # ==========================================

            try:
                config = await get_ticket_settings(guild.id)
            except Exception as error:
                print(f"⚠️ Ticket settings error: {error}")
                config = None

            support_role_id = (
                config.get("support_role_id")
                if config
                else None
            )

            is_support = (
                support_role_id
                and isinstance(interaction.user, discord.Member)
                and any(
                    role.id == support_role_id
                    for role in interaction.user.roles
                )
            )

            # ==========================================
            # GET TICKET DATA
            # ==========================================

            topic = channel.topic or ""

            ticket = {
                "channel_id": channel.id,
                "user_id": None,
                "reason": "Not provided",
                "name": "Unknown",
                "category": "Other",
                "ticket_number": "Unknown",
                "status": "open"
            }

            if "Number:" in topic:
                try:
                    number_part = topic.split("Number:", 1)[1]
                    if "|" in number_part:
                        number_part = number_part.split("|", 1)[0]
                    ticket["ticket_number"] = number_part.strip()
                except Exception as error:
                    print(f"⚠️ Could not read ticket number: {error}")

            if "Category:" in topic:
                try:
                    category_part = topic.split("Category:", 1)[1]
                    if "|" in category_part:
                        category_part = category_part.split("|", 1)[0]
                    ticket["category"] = category_part.strip() or "Other"
                except Exception as error:
                    print(f"⚠️ Could not read ticket category: {error}")

            if "Owner:" in topic:
                try:
                    owner_part = topic.split("Owner:", 1)[1]
                    owner_id_text = owner_part.split("|", 1)[0].strip()
                    ticket["user_id"] = int(owner_id_text)
                except Exception as error:
                    print(f"⚠️ Could not read ticket owner: {error}")

            if "Name:" in topic:
                try:
                    name_part = topic.split("Name:", 1)[1]
                    if "|" in name_part:
                        name_part = name_part.split("|", 1)[0]
                    ticket["name"] = name_part.strip() or "Unknown"
                except Exception as error:
                    print(f"⚠️ Could not read ticket name: {error}")

            if "Reason:" in topic:
                try:
                    reason_part = topic.split("Reason:", 1)[1]
                    if "|" in reason_part:
                        reason_part = reason_part.split("|", 1)[0]
                    ticket["reason"] = reason_part.strip() or "Not provided"
                except Exception as error:
                    print(f"⚠️ Could not read ticket reason: {error}")

            # Database fallback for older tickets.
            if ticket["user_id"] is None:
                try:
                    db_ticket = await get_ticket(guild.id, channel.id)
                    if db_ticket:
                        ticket.update(db_ticket)
                except Exception as error:
                    print(f"⚠️ Database ticket lookup failed: {error}")

            is_owner = ticket.get("user_id") == interaction.user.id

            if not is_owner and not is_support:
                return await interaction.followup.send(
                    "❌ You don't have permission to close this ticket.",
                    ephemeral=True
                )

            owner_id = ticket.get("user_id")
            reason = str(ticket.get("reason", "Not provided"))
            close_reason = str(self.close_reason.value).strip()
            old_name = channel.name

            # ==========================================
            # CLOSE DISCORD CHANNEL FIRST
            # ==========================================
            # Discord-side closing is intentionally done BEFORE
            # the database update so a database problem cannot
            # prevent the ticket from closing.

            # Hide the ticket owner.
            if isinstance(owner_id, int):
                owner = guild.get_member(owner_id)

                if owner:
                    try:
                        await channel.set_permissions(
                            owner,
                            view_channel=False,
                            send_messages=False,
                            reason=f"Iris Ticket closed by {interaction.user}"
                        )
                    except Exception as error:
                        print(f"⚠️ Failed to hide owner: {error}")

            # Rename channel.
            if old_name.startswith("closed-"):
                new_name = old_name
            else:
                new_name = f"closed-{old_name}"

            try:
                await channel.edit(
                    name=new_name[:100],
                    topic=(
                        f"Iris Ticket Closed | "
                        f"Number: {ticket.get('ticket_number', 'Unknown')} | "
                        f"Category: {ticket.get('category', 'Other')} | "
                        f"Owner: {owner_id} | "
                        f"Name: {ticket.get('name', 'Unknown')} | "
                        f"Reason: {reason[:400]} | "
                        f"Close Reason: {close_reason[:250]} | "
                        f"Closed By: {interaction.user.id}"
                    )[:1024],
                    reason=f"Iris Ticket closed by {interaction.user}"
                )
            except Exception as error:
                print(f"⚠️ Channel close/edit failed: {error}")
                new_name = channel.name

            # ==========================================
            # CLOSED EMBED
            # ==========================================

            embed = IrisEmbed.warning(
                "🔒 Iris Ticket Closed",
                (
                    f"This ticket was closed by "
                    f"{interaction.user.mention}.\n\n"
                    "The conversation has been preserved.\n"
                    "A support member can now reopen or delete the "
                    "ticket."
                )
            )

            embed.add_field(
                name="🎫 Ticket",
                value=f"`#{new_name}`",
                inline=True
            )

            embed.add_field(
                name="📂 Category",
                value=str(ticket.get("category", "Other"))[:1024],
                inline=True
            )

            embed.add_field(
                name="📝 Close Reason",
                value=close_reason[:1024],
                inline=False
            )

            embed.add_field(
                name="🔒 Closed By",
                value=interaction.user.mention,
                inline=True
            )

            embed.set_footer(text="Iris • Ticket System")
            embed.timestamp = discord.utils.utcnow()

            # Send the closed-ticket controls.
            try:
                await channel.send(
                    embed=embed,
                    view=ClosedTicketView()
                )
            except Exception as error:
                print(f"❌ Failed to send closed ticket message: {error}")

            # ==========================================
            # DATABASE UPDATE
            # ==========================================

            try:
                # Give the database a few seconds, but never allow
                # a database hang to keep the Discord ticket stuck.
                await asyncio.wait_for(
                    close_ticket(guild.id, channel.id),
                    timeout=5
                )
            except asyncio.TimeoutError:
                print("⚠️ Database close timed out. Discord ticket was still closed.")
            except Exception as error:
                print(f"⚠️ Database close failed: {error}")

            # ==========================================
            # CLOSE LOG
            # ==========================================

            await send_ticket_log(
                guild,
                config,
                "🔒 Iris Ticket Closed",
                (
                    f"**Ticket:** `#{new_name}`\n"
                    f"**Closed By:** {interaction.user.mention}\n"
                    f"**Ticket Reason:** {reason[:600]}\n"
                    f"**Close Reason:** {close_reason[:700]}"
                ),
                success=False
            )

            # ==========================================
            # FINAL CONFIRMATION
            # ==========================================

            try:
                await interaction.edit_original_response(
                    content="✅ Ticket closed successfully with a close reason."
                )
            except Exception as error:
                print(f"⚠️ Could not update close confirmation: {error}")

        except Exception as error:
            print("❌ CLOSE TICKET ERROR:")
            print(repr(error))

            try:
                await interaction.followup.send(
                    (
                        "❌ Something went wrong while closing the ticket.\n"
                        "Check the bot console for the error."
                    ),
                    ephemeral=True
                )
            except Exception:
                pass


# ==========================================
# CLOSED TICKET CONTROLS
# ==========================================

class ClosedTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Reopen Ticket",
        emoji="🔄",
        style=discord.ButtonStyle.success,
        custom_id="iris:reopen_ticket"
    )
    async def reopen_ticket_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        # Acknowledge immediately. Reopen must never wait on MongoDB before
        # Discord receives the interaction acknowledgement.
        try:
            await interaction.response.defer(ephemeral=True)
        except Exception as error:
            print(f"❌ Failed to acknowledge reopen interaction: {error}")
            return

        try:
            config = await asyncio.wait_for(
                get_ticket_settings(guild.id),
                timeout=3
            )
        except Exception as error:
            print(f"⚠️ Ticket settings lookup failed during reopen: {error}")
            config = None

        support_role_id = config.get("support_role_id") if config else None

        # Fallback to the role already present in the ticket permissions.
        if not support_role_id:
            try:
                for target, overwrite in channel.overwrites.items():
                    if (
                        isinstance(target, discord.Role)
                        and overwrite.view_channel is True
                        and overwrite.send_messages is True
                        and overwrite.manage_messages is True
                    ):
                        support_role_id = target.id
                        break
            except Exception:
                pass

        is_support = (
            support_role_id
            and isinstance(interaction.user, discord.Member)
            and any(role.id == support_role_id for role in interaction.user.roles)
        )

        if not is_support:
            return await interaction.followup.send(
                "❌ Only the support team can reopen tickets.",
                ephemeral=True
            )

        topic = channel.topic or ""

        # ==========================================
        # RECOVER TICKET INFORMATION FROM TOPIC
        # ==========================================

        ticket = {
            "channel_id": channel.id,
            "user_id": None,
            "reason": "Not provided",
            "name": "Unknown",
            "category": "Other",
            "ticket_number": "Unknown"
        }

        parsers = {
            "ticket_number": "Number:",
            "category": "Category:",
            "user_id": "Owner:",
            "name": "Name:",
            "reason": "Reason:"
        }

        for key, marker in parsers.items():
            if marker not in topic:
                continue
            try:
                value = topic.split(marker, 1)[1]
                if "|" in value:
                    value = value.split("|", 1)[0]
                value = value.strip()
                if key == "user_id":
                    ticket[key] = int(value)
                elif value:
                    ticket[key] = value
            except Exception:
                pass

        owner_id = ticket.get("user_id")
        owner = guild.get_member(owner_id) if isinstance(owner_id, int) else None

        # ==========================================
        # RESTORE OWNER ACCESS
        # ==========================================

        if owner:
            try:
                await channel.set_permissions(
                    owner,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    reason=f"Iris Ticket reopened by {interaction.user}"
                )
            except discord.Forbidden:
                return await interaction.followup.send(
                    "❌ I don't have permission to restore the ticket owner's access.",
                    ephemeral=True
                )
            except Exception as error:
                print(f"⚠️ Could not restore owner permissions: {error}")

        # ==========================================
        # RESTORE SUPPORT ROLE
        # ==========================================

        support_role = guild.get_role(support_role_id) if support_role_id else None
        if support_role:
            try:
                await channel.set_permissions(
                    support_role,
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                    manage_messages=True,
                    reason=f"Iris Ticket reopened by {interaction.user}"
                )
            except Exception as error:
                print(f"⚠️ Could not restore support permissions: {error}")

        # ==========================================
        # RENAME + RESTORE CLEAN OPEN TOPIC
        # ==========================================

        old_name = channel.name
        new_name = old_name[len("closed-"):] if old_name.startswith("closed-") else old_name

        # IMPORTANT: do not carry Claimed By into the reopened topic.
        # This guarantees the new Claim button starts fresh.
        open_topic = (
            f"Iris Ticket | "
            f"Number: {ticket.get('ticket_number', 'Unknown')} | "
            f"Category: {ticket.get('category', 'Other')} | "
            f"Owner: {owner_id} | "
            f"Name: {ticket.get('name', 'Unknown')} | "
            f"Reason: {str(ticket.get('reason', 'Not provided'))[:650]}"
        )[:1024]

        try:
            await channel.edit(
                name=new_name[:100],
                topic=open_topic,
                reason=f"Iris Ticket reopened by {interaction.user}"
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ I don't have permission to reopen this ticket.",
                ephemeral=True
            )
        except Exception as error:
            print(f"❌ Ticket reopen channel edit failed: {error}")
            return await interaction.followup.send(
                "❌ I couldn't reopen this ticket.",
                ephemeral=True
            )

        # ==========================================
        # DATABASE STATUS — NON-BLOCKING
        # ==========================================
        # Discord is the source of truth for the immediate reopen action.
        # If the DB is available, update it in the background; never make the
        # button wait for MongoDB.
        async def update_reopen_database():
            try:
                ticket_collection = (
                    getattr(database, "tickets", None)
                    or getattr(database, "ticket", None)
                    or getattr(database, "ticket_collection", None)
                )
                if ticket_collection is None:
                    return

                await asyncio.wait_for(
                    ticket_collection.update_one(
                        {"guild_id": guild.id, "channel_id": channel.id},
                        {
                            "$set": {
                                "status": "open",
                                "user_id": ticket.get("user_id"),
                                "reason": ticket.get("reason", "Not provided"),
                                "name": ticket.get("name", "Unknown"),
                                "category": ticket.get("category", "Other"),
                                "ticket_number": ticket.get("ticket_number", "Unknown")
                            },
                            "$unset": {
                                "claimed_by": "",
                                "claimed_at": ""
                            }
                        },
                        upsert=False
                    ),
                    timeout=2
                )
            except Exception as error:
                print(f"⚠️ Background ticket reopen database update failed: {error}")

        asyncio.create_task(update_reopen_database())

        # ==========================================
        # REOPEN MESSAGE + FRESH CONTROLS
        # ==========================================

        embed = IrisEmbed.success(
            "🔄 Iris Ticket Reopened",
            (
                f"This ticket has been reopened by {interaction.user.mention}.\n\n"
                "The ticket owner can access the ticket again and the "
                "support team can continue assisting.\n\n"
                "🎟️ **Claim Ticket** is ready for a fresh claim."
            )
        )

        embed.add_field(
            name="🎫 Ticket",
            value=f"`#{new_name}`",
            inline=True
        )
        embed.add_field(
            name="📂 Category",
            value=str(ticket.get("category", "Other"))[:1024],
            inline=True
        )
        embed.add_field(
            name="🔄 Reopened By",
            value=interaction.user.mention,
            inline=True
        )
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(
                embed=embed,
                view=TicketControlView()
            )
        except Exception as error:
            print(f"❌ Failed to send reopened ticket controls: {error}")

        if config:
            await send_ticket_log(
                guild,
                config,
                "🔄 Iris Ticket Reopened",
                (
                    f"**Ticket:** `#{new_name}`\n"
                    f"**Ticket Number:** `#{ticket.get('ticket_number', 'Unknown')}`\n"
                    f"**Category:** {ticket.get('category', 'Other')}\n"
                    f"**Reopened By:** {interaction.user.mention}"
                ),
                success=True
            )

        # Disable the old closed-ticket buttons.
        for child in self.children:
            child.disabled = True

        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.followup.send(
            "✅ Ticket reopened successfully — Claim Ticket is ready.",
            ephemeral=True
        )


    @discord.ui.button(
        label="Delete Ticket",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="iris:delete_ticket"
    )
    async def delete_ticket_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(
            channel,
            discord.TextChannel
        ):

            return await interaction.response.send_message(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        config = await get_ticket_settings(
            guild.id
        )

        # ==========================================
        # CHECK SUPPORT ROLE
        # ==========================================

        support_role_id = (
            config.get("support_role_id")
            if config
            else None
        )

        is_support = (
            support_role_id
            and isinstance(
                interaction.user,
                discord.Member
            )
            and any(
                role.id == support_role_id
                for role in interaction.user.roles
            )
        )

        if not is_support:

            return await interaction.response.send_message(
                "❌ Only the support team can delete tickets.",
                ephemeral=True
            )

        await interaction.response.defer(
            ephemeral=True
        )

        # ==========================================
        # GET TICKET
        # ==========================================

        ticket = await get_ticket(
            guild.id,
            channel.id
        )

        # ==========================================
        # RECOVER TICKET DATA FROM TOPIC
        # ==========================================

        if not ticket:

            ticket = {
                "channel_id": channel.id,
                "user_id": None,
                "reason": "Not available",
                "name": "Unknown",
                "category": "Other",
                "ticket_number": "Unknown",
                "status": "closed"
            }

            topic = channel.topic or ""

            if "Number:" in topic:
                try:
                    number_part = topic.split("Number:", 1)[1]
                    if "|" in number_part:
                        number_part = number_part.split("|", 1)[0]
                    ticket["ticket_number"] = number_part.strip()
                except Exception:
                    pass

            if "Category:" in topic:
                try:
                    category_part = topic.split("Category:", 1)[1]
                    if "|" in category_part:
                        category_part = category_part.split("|", 1)[0]
                    ticket["category"] = category_part.strip()
                except Exception:
                    pass

            if "Owner:" in topic:

                try:

                    owner_part = topic.split(
                        "Owner:",
                        1
                    )[1]

                    owner_id = owner_part.split(
                        "|",
                        1
                    )[0].strip()

                    ticket["user_id"] = int(
                        owner_id
                    )

                except Exception:
                    pass

            if "Name:" in topic:

                try:

                    name_part = topic.split("Name:", 1)[1]
                    if "|" in name_part:
                        name_part = name_part.split("|", 1)[0]
                    ticket["name"] = name_part.strip()

                except Exception:
                    pass

            if "Reason:" in topic:

                try:

                    reason_part = topic.split(
                        "Reason:",
                        1
                    )[1]

                    if "|" in reason_part:

                        reason_part = reason_part.split(
                            "|",
                            1
                        )[0]

                    ticket["reason"] = (
                        reason_part.strip()
                    )

                except Exception:
                    pass

        # ==========================================
        # GENERATE HTML TRANSCRIPT
        # ==========================================

        try:

            transcript = await create_ticket_transcript(
                channel,
                ticket,
                interaction.user,
                interaction.user
            )

            transcript_file = discord.File(
                io.BytesIO(
                    transcript.encode("utf-8")
                ),
                filename=(
                    f"iris-ticket-{channel.id}.html"
                )
            )

            log_channel_id = (
                config.get("log_channel_id")
                if config
                else None
            )

            log_channel = (
                guild.get_channel(
                    log_channel_id
                )
                if log_channel_id
                else None
            )

            # ==========================================
            # SEND TRANSCRIPT
            # ==========================================

            if log_channel:

                embed = IrisEmbed.success(
                    "📜 Iris Ticket Transcript",
                    (
                        f"Transcript for "
                        f"**#{channel.name}**\n\n"
                        f"🗑️ Deleted by "
                        f"{interaction.user.mention}"
                    )
                )

                if ticket.get("user_id"):

                    embed.add_field(
                        name="👤 Ticket Owner",
                        value=(
                            f"<@{ticket.get('user_id')}>"
                        ),
                        inline=True
                    )

                embed.add_field(
                    name="📂 Category",
                    value=str(ticket.get("category", "Other"))[:1024],
                    inline=True
                )

                embed.add_field(
                    name="📝 Reason",
                    value=str(
                        ticket.get(
                            "reason",
                            "Not provided"
                        )
                    )[:1024],
                    inline=False
                )

                embed.set_footer(
                    text="Iris • Ticket Logs"
                )

                embed.timestamp = (
                    discord.utils.utcnow()
                )

                await log_channel.send(
                    embed=embed,
                    file=transcript_file
                )

        except Exception as error:

            print(
                f"❌ Transcript error: {error}"
            )

        # ==========================================
        # DELETE LOG
        # ==========================================

        await send_ticket_log(
            guild,
            config,
            "🗑️ Iris Ticket Deleted",
            (
                f"**Channel:** `{channel.name}`\n"
                f"**Category:** {ticket.get('category', 'Other')}\n"
                f"**Deleted By:** "
                f"{interaction.user.mention}\n"
                f"📜 **Transcript:** Generated"
            ),
            success=False
        )

        # ==========================================
        # CONFIRM
        # ==========================================

        await interaction.followup.send(
            "📜 Transcript saved. 🗑️ Deleting ticket...",
            ephemeral=True
        )

        # ==========================================
        # DELETE CHANNEL
        # ==========================================

        try:

            await channel.delete(
                reason=(
                    f"Iris Ticket deleted by "
                    f"{interaction.user}"
                )
            )

        except discord.Forbidden:

            print(
                "❌ Iris does not have permission "
                "to delete the ticket channel."
            )

        except Exception as error:

            print(
                f"❌ Ticket deletion error: {error}"
            )


# ==========================================
# CREATE HTML TRANSCRIPT
# ==========================================

async def create_ticket_transcript(
    channel: discord.TextChannel,
    ticket: dict,
    closed_by: discord.Member,
    deleted_by: discord.Member
):

    messages_html = []

    async for message in channel.history(limit=None, oldest_first=True):

        timestamp = message.created_at.strftime("%d %b %Y • %H:%M UTC")
        author_name = html.escape(message.author.display_name)
        author_tag = html.escape(str(message.author))
        avatar_url = html.escape(message.author.display_avatar.url)

        content_html = ""
        if message.content:
            content_html = (
                '<div class="content">'
                f'{html.escape(message.content)}'
                '</div>'
            )

        embeds_html = ""

        for embed in message.embeds:
            embed_color = "#5865f2"

            if embed.color:
                try:
                    embed_color = f"#{embed.color.value:06x}"
                except Exception:
                    pass

            author_html = ""
            if embed.author and embed.author.name:
                icon_html = ""
                if embed.author.icon_url:
                    icon_html = (
                        f'<img class="embed-author-icon" '
                        f'src="{html.escape(str(embed.author.icon_url))}">'
                    )

                author_html = f'''
                <div class="embed-author">
                    {icon_html}
                    <span>{html.escape(embed.author.name)}</span>
                </div>
                '''

            title_html = ""
            if embed.title:
                title_html = (
                    f'<div class="embed-title">'
                    f'{html.escape(embed.title)}</div>'
                )

            description_html = ""
            if embed.description:
                description_html = (
                    f'<div class="embed-description">'
                    f'{html.escape(embed.description)}</div>'
                )

            fields_html = ""
            for field in embed.fields:
                fields_html += f'''
                <div class="embed-field">
                    <div class="embed-field-name">{html.escape(str(field.name))}</div>
                    <div class="embed-field-value">{html.escape(str(field.value))}</div>
                </div>
                '''

            thumbnail_html = ""
            if embed.thumbnail and embed.thumbnail.url:
                thumbnail_html = (
                    f'<img class="embed-thumbnail" '
                    f'src="{html.escape(str(embed.thumbnail.url))}">'
                )

            image_html = ""
            if embed.image and embed.image.url:
                image_html = (
                    f'<img class="embed-image" '
                    f'src="{html.escape(str(embed.image.url))}">'
                )

            footer_html = ""
            if embed.footer and embed.footer.text:
                footer_html = f'''
                <div class="embed-footer">
                    {html.escape(embed.footer.text)}
                </div>
                '''

            embeds_html += f'''
            <div class="discord-embed" style="--embed-color:{embed_color}">
                {author_html}
                <div class="embed-main">
                    <div class="embed-text">
                        {title_html}
                        {description_html}
                        {fields_html}
                        {footer_html}
                    </div>
                    {thumbnail_html}
                </div>
                {image_html}
            </div>
            '''

        attachments_html = ""

        for attachment in message.attachments:
            attachment_url = html.escape(attachment.url)
            attachment_name = html.escape(attachment.filename)

            if attachment.content_type and attachment.content_type.startswith("image/"):
                attachments_html += f'''
                <div class="attachment">
                    <a href="{attachment_url}" target="_blank">
                        <img class="attachment-image" src="{attachment_url}">
                    </a>
                    <div class="attachment-name">📎 {attachment_name}</div>
                </div>
                '''
            else:
                attachments_html += f'''
                <div class="attachment file-attachment">
                    <span>📎</span>
                    <a href="{attachment_url}" target="_blank">{attachment_name}</a>
                </div>
                '''

        stickers_html = ""
        for sticker in message.stickers:
            stickers_html += f'''
            <div class="sticker">🏷️ {html.escape(sticker.name)}</div>
            '''

        if not content_html and not embeds_html and not attachments_html and not stickers_html:
            continue

        bot_badge = '<span class="bot-badge">BOT</span>' if message.author.bot else ''

        messages_html.append(f'''
        <article class="message">
            <img class="avatar" src="{avatar_url}" alt="">
            <div class="message-body">
                <div class="message-header">
                    <span class="author-name">{author_name}</span>
                    {bot_badge}
                    <span class="author-tag">{author_tag}</span>
                    <span class="timestamp">{timestamp}</span>
                </div>
                {content_html}
                {embeds_html}
                {attachments_html}
                {stickers_html}
            </div>
        </article>
        ''')

    owner_id = ticket.get("user_id", "Unknown")
    ticket_display_name = ticket.get("name", "Unknown")
    ticket_number = ticket.get("ticket_number", "Unknown")
    ticket_category = ticket.get("category", "Other")

    # Close reason is stored in the closed ticket topic.
    close_reason = "Not provided"
    topic = channel.topic or ""
    if "Close Reason:" in topic:
        try:
            close_reason_part = topic.split("Close Reason:", 1)[1]
            if "|" in close_reason_part:
                close_reason_part = close_reason_part.split("|", 1)[0]
            close_reason = close_reason_part.strip() or "Not provided"
        except Exception:
            pass

    if ticket_display_name == "Unknown":
        topic = channel.topic or ""
        if "Name:" in topic:
            try:
                name_part = topic.split("Name:", 1)[1]
                if "|" in name_part:
                    name_part = name_part.split("|", 1)[0]
                ticket_display_name = name_part.strip() or "Unknown"
            except Exception:
                pass

    if ticket_category == "Other" and "Category:" in topic:
        try:
            category_part = topic.split("Category:", 1)[1]
            if "|" in category_part:
                category_part = category_part.split("|", 1)[0]
            ticket_category = category_part.strip() or "Other"
        except Exception:
            pass

    if ticket_number == "Unknown" and "Number:" in topic:
        try:
            number_part = topic.split("Number:", 1)[1]
            if "|" in number_part:
                number_part = number_part.split("|", 1)[0]
            ticket_number = number_part.strip() or "Unknown"
        except Exception:
            pass

    ticket_display_name = html.escape(str(ticket_display_name))
    ticket_category = html.escape(str(ticket_category))
    ticket_number = html.escape(str(ticket_number))
    reason = html.escape(str(ticket.get("reason", "No reason provided")))
    close_reason = html.escape(str(close_reason))
    ticket_name = html.escape(channel.name)
    closed_by_name = html.escape(str(closed_by))
    deleted_by_name = html.escape(str(deleted_by))

    transcript = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Iris Ticket • {ticket_name}</title>
<style>
* {{ box-sizing: border-box; }}
body {{
    margin: 0;
    background: #0f1014;
    color: #dcdee1;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.45;
}}
a {{ color: #00a8fc; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
.container {{ width: min(1050px, calc(100% - 32px)); margin: 30px auto 50px; }}
.header {{
    background: linear-gradient(135deg, #1e2027, #17181d);
    border: 1px solid #2b2d33;
    border-radius: 16px;
    padding: 26px 28px;
    margin-bottom: 14px;
    box-shadow: 0 8px 30px rgba(0,0,0,.22);
}}
.brand {{ color: #949ba4; font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; margin-bottom: 7px; }}
.header h1 {{ margin: 0; color: #fff; font-size: 28px; }}
.header p {{ margin: 7px 0 0; color: #aeb4bc; }}
.info {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 9px; margin-bottom: 14px; }}
.info-card {{ background: #181a1f; border: 1px solid #292c32; border-radius: 11px; padding: 13px 15px; min-width: 0; }}
.info-card.reason {{ grid-column: 1 / -1; }}
.info-label {{ color: #8e949d; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .06em; margin-bottom: 4px; }}
.info-value {{ color: #f2f3f5; font-size: 13px; overflow-wrap: anywhere; }}
.conversation {{ background: #141519; border: 1px solid #292c32; border-radius: 16px; overflow: hidden; }}
.conversation-header {{ padding: 15px 20px; background: #191b20; border-bottom: 1px solid #292c32; font-size: 15px; font-weight: 700; }}
.messages {{ padding: 4px 20px 14px; }}
.message {{ display: flex; gap: 12px; padding: 14px 0; border-bottom: 1px solid #25272d; }}
.message:last-child {{ border-bottom: 0; }}
.avatar {{ width: 40px; height: 40px; border-radius: 50%; object-fit: cover; flex: 0 0 40px; background: #202228; }}
.message-body {{ min-width: 0; flex: 1; }}
.message-header {{ display: flex; align-items: baseline; flex-wrap: wrap; gap: 6px; margin-bottom: 4px; }}
.author-name {{ font-weight: 700; color: #f2f3f5; }}
.author-tag {{ color: #727985; font-size: 11px; }}
.timestamp {{ color: #727985; font-size: 10px; margin-left: 2px; }}
.bot-badge {{ background: #5865f2; color: #fff; border-radius: 4px; padding: 1px 4px; font-size: 8px; font-weight: 800; }}
.content {{ color: #dbdee1; white-space: pre-wrap; overflow-wrap: anywhere; word-break: break-word; font-size: 14px; }}
.discord-embed {{ margin-top: 7px; background: #1e2025; border-left: 4px solid var(--embed-color, #5865f2); border-radius: 5px; padding: 11px 13px; max-width: 760px; overflow: hidden; }}
.embed-author {{ display: flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 700; margin-bottom: 6px; }}
.embed-author-icon {{ width: 21px; height: 21px; border-radius: 50%; object-fit: cover; }}
.embed-main {{ display: flex; gap: 13px; align-items: flex-start; }}
.embed-text {{ min-width: 0; flex: 1; }}
.embed-title {{ color: #fff; font-size: 15px; font-weight: 700; margin-bottom: 5px; }}
.embed-description {{ color: #dbdee1; font-size: 13px; white-space: pre-wrap; overflow-wrap: anywhere; }}
.embed-field {{ margin-top: 9px; }}
.embed-field-name {{ color: #fff; font-size: 12px; font-weight: 700; margin-bottom: 2px; }}
.embed-field-value {{ color: #c7cbd1; font-size: 12px; white-space: pre-wrap; overflow-wrap: anywhere; }}
.embed-thumbnail {{ width: 68px; height: 68px; border-radius: 5px; object-fit: cover; flex: 0 0 68px; }}
.embed-image {{ display: block; width: auto; max-width: 100%; max-height: 400px; border-radius: 5px; margin-top: 9px; object-fit: contain; }}
.embed-footer {{ color: #8e949d; font-size: 10px; margin-top: 9px; }}
.attachment {{ margin-top: 8px; }}
.attachment-image {{ display: block; max-width: min(650px, 100%); max-height: 450px; border-radius: 8px; object-fit: contain; }}
.attachment-name {{ color: #8e949d; font-size: 10px; margin-top: 3px; }}
.file-attachment {{ display: inline-flex; align-items: center; gap: 6px; background: #1e2025; border: 1px solid #30333a; border-radius: 7px; padding: 7px 9px; font-size: 12px; }}
.sticker {{ display: inline-block; margin-top: 7px; padding: 5px 8px; background: #1e2025; border-radius: 6px; color: #b8bec7; font-size: 11px; }}
.footer {{ text-align: center; color: #686f79; font-size: 11px; padding: 20px 0; }}
@media (max-width: 760px) {{
    .container {{ width: calc(100% - 16px); margin-top: 10px; }}
    .info {{ grid-template-columns: 1fr 1fr; }}
    .header {{ padding: 20px; }}
    .header h1 {{ font-size: 22px; }}
    .messages {{ padding-left: 12px; padding-right: 12px; }}
}}
@media (max-width: 480px) {{
    .info {{ grid-template-columns: 1fr; }}
    .info-card.reason {{ grid-column: auto; }}
    .avatar {{ width: 34px; height: 34px; flex-basis: 34px; }}
    .message {{ gap: 9px; }}
    .author-tag {{ display: none; }}
    .embed-thumbnail {{ width: 55px; height: 55px; flex-basis: 55px; }}
}}
</style>
</head>
<body>
<div class="container">
    <header class="header">
        <div class="brand">🎫 Iris • Ticket System</div>
        <h1>Ticket Transcript</h1>
        <p>Complete conversation for <strong>#{ticket_name}</strong></p>
    </header>

    <section class="info">
        <div class="info-card"><div class="info-label">Ticket</div><div class="info-value">#{ticket_name}</div></div>
        <div class="info-card"><div class="info-label">Ticket Number</div><div class="info-value">#{ticket_number}</div></div>
        <div class="info-card"><div class="info-label">Category</div><div class="info-value">{ticket_category}</div></div>
        <div class="info-card"><div class="info-label">Owner ID</div><div class="info-value">{owner_id}</div></div>
        <div class="info-card"><div class="info-label">Name</div><div class="info-value">{ticket_display_name}</div></div>
        <div class="info-card"><div class="info-label">Closed By</div><div class="info-value">{closed_by_name}</div></div>
        <div class="info-card"><div class="info-label">Deleted By</div><div class="info-value">{deleted_by_name}</div></div>
        <div class="info-card reason"><div class="info-label">Ticket Reason</div><div class="info-value">{reason}</div></div>
        <div class="info-card reason"><div class="info-label">Close Reason</div><div class="info-value">{close_reason}</div></div>
    </section>

    <section class="conversation">
        <div class="conversation-header">💬 Conversation</div>
        <div class="messages">
            {''.join(messages_html)}
        </div>
    </section>

    <footer class="footer">
        Iris • Ticket System<br>
        Transcript generated automatically
    </footer>
</div>
</body>
</html>
'''

    return transcript


# ==========================================
# TICKET LOGGING
# ==========================================

async def send_ticket_log(
    guild,
    config,
    title,
    description,
    success=False
):

    if not config:
        return

    log_channel_id = config.get(
        "log_channel_id"
    )

    if not log_channel_id:
        return

    log_channel = guild.get_channel(
        log_channel_id
    )

    if log_channel is None:
        return

    if success:

        embed = IrisEmbed.success(
            title,
            description
        )

    else:

        embed = IrisEmbed.warning(
            title,
            description
        )

    embed.set_footer(
        text="Iris • Ticket Logs"
    )

    embed.timestamp = discord.utils.utcnow()

    try:

        await log_channel.send(
            embed=embed
        )

    except Exception as error:

        print(
            f"❌ Failed to send ticket log: {error}"
        )


# ==========================================
# TICKETS COG
# ==========================================

class TicketResetConfirmView(discord.ui.View):

    def __init__(self, bot, author_id, guild_id):
        super().__init__(timeout=60)
        self.bot = bot
        self.author_id = author_id
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ Only the person who started the reset can confirm it.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="Reset & Clear Logs",
        emoji="🗑️",
        style=discord.ButtonStyle.danger,
        custom_id="iris:confirm_ticket_reset"
    )
    async def confirm_reset(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer(ephemeral=True)

        try:
            # Reset the persistent counter to zero.
            await settings.update_one(
                {"guild_id": self.guild_id},
                {"$set": {"ticket_counter": 0}},
                upsert=True
            )

            config = await get_ticket_settings(
                self.guild_id
            )

            deleted_count = 0

            # Clear Iris-authored messages from the configured ticket log channel.
            if config and config.get("log_channel_id"):

                log_channel = interaction.guild.get_channel(
                    config.get("log_channel_id")
                )

                if isinstance(log_channel, discord.TextChannel):

                    me = interaction.guild.me

                    if me and log_channel.permissions_for(me).manage_messages:

                        try:
                            deleted = await log_channel.purge(
                                limit=None,
                                check=lambda message: (
                                    message.author.id
                                    == self.bot.user.id
                                ),
                                bulk=True
                            )

                            deleted_count = len(deleted)

                        except Exception as error:
                            print(
                                f"⚠️ Could not clear ticket logs: {error}"
                            )

            # Disable the confirmation buttons.
            for child in self.children:
                child.disabled = True

            await interaction.edit_original_response(
                content=(
                    "✅ **Ticket system reset successfully.**\n\n"
                    "🔢 Counter reset → **#0001**\n"
                    f"🗑️ Iris log messages deleted → **{deleted_count}**\n\n"
                    "The next ticket created will be **0001**."
                ),
                view=self
            )

        except Exception as error:

            print(
                f"❌ Ticket reset error: {error}"
            )

            await interaction.edit_original_response(
                content=(
                    "❌ The ticket reset failed. "
                    "Check the bot console for the error."
                ),
                view=None
            )

    @discord.ui.button(
        label="Cancel",
        emoji="✖️",
        style=discord.ButtonStyle.secondary,
        custom_id="iris:cancel_ticket_reset"
    )
    async def cancel_reset(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content="❎ Ticket reset cancelled. Nothing was changed.",
            view=self
        )


class Tickets(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        print(
            "🔥 Tickets COG INITIALIZED"
        )

    # ==========================================
    # TICKET STATISTICS
    # ==========================================

    @app_commands.command(
        name="ticketstats",
        description="Show ticket statistics for this server."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketstats(
        self,
        interaction: discord.Interaction
    ):
        """Show live ticket statistics using the server's ticket channels."""

        guild = interaction.guild

        if guild is None:
            return await interaction.response.send_message(
                "❌ This command can only be used in a server.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # Ticket numbers are persisted in the settings counter.
        try:
            counter_doc = await asyncio.wait_for(
                settings.find_one(
                    {"guild_id": guild.id},
                    {"ticket_counter": 1}
                ),
                timeout=3
            )
            total_created = int(
                (counter_doc or {}).get("ticket_counter", 0)
            )
        except Exception as error:
            print(f"⚠️ Ticket stats counter lookup failed: {error}")
            total_created = 0

        # Count tickets that currently exist as Discord channels.
        open_count = 0
        closed_count = 0

        for channel in guild.text_channels:
            topic = channel.topic or ""

            if not (
                topic.startswith("Iris Ticket |")
                or topic.startswith("Iris Ticket Closed |")
            ):
                continue

            if channel.name.startswith("closed-"):
                closed_count += 1
            else:
                open_count += 1

        # Deleted tickets are estimated from the persistent counter.
        # This keeps the command useful even though deleted channels no
        # longer exist in Discord.
        deleted_count = max(
            0,
            total_created - open_count - closed_count
        )

        embed = IrisEmbed.success(
            "📊 Iris Ticket Statistics",
            "Live ticket statistics for this server."
        )

        embed.add_field(
            name="🎫 Total Tickets",
            value=f"`{total_created}`",
            inline=True
        )

        embed.add_field(
            name="🟢 Open",
            value=f"`{open_count}`",
            inline=True
        )

        embed.add_field(
            name="🔒 Closed",
            value=f"`{closed_count}`",
            inline=True
        )

        embed.add_field(
            name="🗑️ Deleted",
            value=f"`{deleted_count}`",
            inline=True
        )

        embed.add_field(
            name="📌 Note",
            value=(
                "Deleted tickets are calculated from the persistent ticket "
                "counter because deleted Discord channels no longer exist "
                "to be counted directly."
            ),
            inline=False
        )

        embed.set_footer(
            text="Iris • Ticket Statistics"
        )
        embed.timestamp = discord.utils.utcnow()

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )


    # ==========================================
    # TICKET ACCESS HELPERS
    # ==========================================

    async def _get_ticket_context(self, interaction: discord.Interaction):
        """Return ticket context for ticket member-management commands."""
        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel) or guild is None:
            await interaction.response.send_message(
                "❌ This command can only be used inside a ticket channel.",
                ephemeral=True
            )
            return None

        topic = channel.topic or ""
        if not topic.startswith("Iris Ticket |"):
            await interaction.response.send_message(
                "❌ This is not an Iris ticket channel.",
                ephemeral=True
            )
            return None

        config = await get_ticket_settings(guild.id)
        support_role_id = config.get("support_role_id") if config else None

        is_support = (
            bool(support_role_id)
            and isinstance(interaction.user, discord.Member)
            and any(
                role.id == support_role_id
                for role in interaction.user.roles
            )
        )

        try:
            ticket = await get_ticket(guild.id, channel.id)
        except Exception as error:
            print(f"⚠️ Ticket lookup failed: {error}")
            ticket = None

        if not ticket:
            ticket = {
                "channel_id": channel.id,
                "user_id": None,
                "status": "open"
            }

            if "Owner:" in topic:
                try:
                    owner_part = topic.split("Owner:", 1)[1]
                    owner_id = owner_part.split("|", 1)[0].strip()
                    ticket["user_id"] = int(owner_id)
                except Exception:
                    pass

        return channel, guild, config, ticket, is_support

    async def _require_support(
        self,
        interaction: discord.Interaction
    ):
        context = await self._get_ticket_context(interaction)
        if not context:
            return None

        channel, guild, config, ticket, is_support = context

        if not is_support:
            await interaction.response.send_message(
                "❌ Only the **support team** can manage ticket members.",
                ephemeral=True
            )
            return None

        return context

    # ==========================================
    # ADD USER TO TICKET
    # ==========================================

    @app_commands.command(
        name="adduser",
        description="Add a member to the current ticket."
    )
    @app_commands.describe(
        user="The member who should be added to this ticket."
    )
    async def adduser(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        context = await self._require_support(interaction)
        if not context:
            return

        channel, guild, config, ticket, is_support = context

        if user.bot:
            return await interaction.response.send_message(
                "❌ You cannot add a bot to a ticket.",
                ephemeral=True
            )

        try:
            await channel.set_permissions(
                user,
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
                reason=f"Iris Ticket: {interaction.user} added {user}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ I don't have permission to update this ticket's permissions.",
                ephemeral=True
            )
        except Exception as error:
            print(f"❌ Add user error: {error}")
            return await interaction.response.send_message(
                "❌ I couldn't add that member to the ticket.",
                ephemeral=True
            )

        embed = IrisEmbed.success(
            "➕ User Added",
            (
                f"{user.mention} has been added to this ticket by "
                f"{interaction.user.mention}.\n\n"
                "They can now view and participate in this ticket."
            )
        )
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

        await send_ticket_log(
            guild,
            config,
            "➕ Iris Ticket User Added",
            (
                f"**Ticket:** `#{channel.name}`\n"
                f"**User Added:** {user.mention}\n"
                f"**Added By:** {interaction.user.mention}"
            ),
            success=True
        )

    # ==========================================
    # REMOVE USER FROM TICKET
    # ==========================================

    @app_commands.command(
        name="removeuser",
        description="Remove a member from the current ticket."
    )
    @app_commands.describe(
        user="The member who should be removed from this ticket."
    )
    async def removeuser(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):
        context = await self._require_support(interaction)
        if not context:
            return

        channel, guild, config, ticket, is_support = context

        owner_id = ticket.get("user_id")

        if owner_id is None:
            topic = channel.topic or ""
            if "Owner:" in topic:
                try:
                    owner_part = topic.split("Owner:", 1)[1]
                    owner_id = int(
                        owner_part.split("|", 1)[0].strip()
                    )
                except Exception:
                    pass

        if owner_id == user.id:
            return await interaction.response.send_message(
                "❌ You can't remove the **ticket owner** from their own ticket.",
                ephemeral=True
            )

        support_role_id = config.get("support_role_id") if config else None

        if (
            support_role_id
            and any(
                role.id == support_role_id
                for role in user.roles
            )
        ):
            return await interaction.response.send_message(
                "❌ You can't remove a member of the **support team** from the ticket.",
                ephemeral=True
            )

        try:
            await channel.set_permissions(
                user,
                view_channel=False,
                send_messages=False,
                read_message_history=False,
                attach_files=False,
                embed_links=False,
                reason=f"Iris Ticket: {interaction.user} removed {user}"
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ I don't have permission to update this ticket's permissions.",
                ephemeral=True
            )
        except Exception as error:
            print(f"❌ Remove user error: {error}")
            return await interaction.response.send_message(
                "❌ I couldn't remove that member from the ticket.",
                ephemeral=True
            )

        embed = IrisEmbed.warning(
            "➖ User Removed",
            (
                f"{user.mention} has been removed from this ticket by "
                f"{interaction.user.mention}."
            )
        )
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

        await send_ticket_log(
            guild,
            config,
            "➖ Iris Ticket User Removed",
            (
                f"**Ticket:** `#{channel.name}`\n"
                f"**User Removed:** {user.mention}\n"
                f"**Removed By:** {interaction.user.mention}"
            ),
            success=False
        )

    # ==========================================
    # TICKET INFO
    # ==========================================

    @app_commands.command(
        name="ticketinfo",
        description="Show information about the current ticket."
    )
    async def ticketinfo(
        self,
        interaction: discord.Interaction
    ):
        context = await self._get_ticket_context(interaction)
        if not context:
            return

        channel, guild, config, ticket, is_support = context
        topic = channel.topic or ""

        owner_id = ticket.get("user_id")
        if owner_id is None and "Owner:" in topic:
            try:
                owner_id = int(
                    topic.split("Owner:", 1)[1].split("|", 1)[0].strip()
                )
            except Exception:
                owner_id = None

        owner = guild.get_member(owner_id) if isinstance(owner_id, int) else None

        ticket_number = ticket.get("ticket_number")
        if ticket_number is None and "Number:" in topic:
            try:
                ticket_number = int(
                    topic.split("Number:", 1)[1].split("|", 1)[0].strip()
                )
            except Exception:
                ticket_number = "Unknown"

        category = ticket.get("category", "Other")
        if category == "Other" and "Category:" in topic:
            category = topic.split("Category:", 1)[1].split("|", 1)[0].strip() or "Other"

        reason = str(ticket.get("reason", "Not provided"))

        claimed_by = "Not claimed"
        if "Claimed By:" in topic:
            try:
                claimed_id = int(
                    topic.split("Claimed By:", 1)[1].split("|", 1)[0].strip()
                )
                claimed_member = guild.get_member(claimed_id)
                claimed_by = (
                    claimed_member.mention
                    if claimed_member
                    else f"<@{claimed_id}>"
                )
            except Exception:
                pass

        embed = IrisEmbed.success(
            "🎫 Ticket Information",
            f"Information for {channel.mention}"
        )

        embed.add_field(
            name="🔢 Ticket Number",
            value=f"`#{ticket_number:04d}`" if isinstance(ticket_number, int) else f"`{ticket_number}`",
            inline=True
        )
        embed.add_field(
            name="📊 Status",
            value="🟢 Open",
            inline=True
        )
        embed.add_field(
            name="📂 Category",
            value=str(category)[:1024],
            inline=True
        )
        embed.add_field(
            name="👤 Owner",
            value=owner.mention if owner else (
                f"<@{owner_id}>" if owner_id else "Unknown"
            ),
            inline=True
        )
        embed.add_field(
            name="🎟️ Claimed By",
            value=claimed_by,
            inline=True
        )
        embed.add_field(
            name="📝 Reason",
            value=reason[:1024],
            inline=False
        )

        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

    # ==========================================
    # RENAME TICKET
    # ==========================================

    @app_commands.command(
        name="ticketrename",
        description="Rename the current ticket."
    )
    @app_commands.describe(
        name="New ticket name, without the ticket number prefix."
    )
    async def ticketrename(
        self,
        interaction: discord.Interaction,
        name: str
    ):
        # Acknowledge Discord immediately so the interaction can never
        # expire while MongoDB or Discord is processing the rename.
        await interaction.response.defer(ephemeral=True)

        channel = interaction.channel
        guild = interaction.guild

        if not isinstance(channel, discord.TextChannel) or guild is None:
            return await interaction.followup.send(
                "❌ This is not a ticket channel.",
                ephemeral=True
            )

        # Read the ticket identity directly from the channel topic first.
        # This avoids waiting for a full ticket DB lookup just to rename it.
        topic = channel.topic or ""

        if not topic.startswith("Iris Ticket |"):
            return await interaction.followup.send(
                "❌ This is not an open Iris ticket.",
                ephemeral=True
            )

        # Support-role check only needs the server ticket settings.
        try:
            config = await asyncio.wait_for(
                get_ticket_settings(guild.id),
                timeout=3
            )
        except Exception as error:
            print(f"⚠️ Ticket settings lookup failed during rename: {error}")
            return await interaction.followup.send(
                "❌ Iris could not load the ticket settings. Please try again.",
                ephemeral=True
            )

        support_role_id = (
            config.get("support_role_id")
            if config
            else None
        )

        is_support = (
            bool(support_role_id)
            and isinstance(interaction.user, discord.Member)
            and any(
                role.id == support_role_id
                for role in interaction.user.roles
            )
        )

        # Ticket owner can also rename their own ticket.
        owner_id = None
        if "Owner:" in topic:
            try:
                owner_id = int(
                    topic.split("Owner:", 1)[1].split("|", 1)[0].strip()
                )
            except Exception:
                pass

        is_owner = owner_id == interaction.user.id

        if not is_support and not is_owner:
            return await interaction.followup.send(
                "❌ You don't have permission to rename this ticket.",
                ephemeral=True
            )

        cleaned_name = re.sub(
            r"[^a-zA-Z0-9_-]+",
            "-",
            name.strip().lower()
        )
        cleaned_name = re.sub(
            r"-{2,}",
            "-",
            cleaned_name
        ).strip("-_")

        if not cleaned_name:
            return await interaction.followup.send(
                "❌ Please provide a valid ticket name.",
                ephemeral=True
            )

        # Preserve the existing ticket number from the topic.
        ticket_number = None
        if "Number:" in topic:
            try:
                ticket_number = int(
                    topic.split("Number:", 1)[1].split("|", 1)[0].strip()
                )
            except Exception:
                pass

        if isinstance(ticket_number, int):
            new_name = f"ticket-{ticket_number:04d}-{cleaned_name}"
        else:
            new_name = f"ticket-{cleaned_name}"

        new_name = new_name[:100]
        old_name = channel.name

        if old_name == new_name:
            return await interaction.followup.send(
                "ℹ️ The ticket already has that name.",
                ephemeral=True
            )

        try:
            await channel.edit(
                name=new_name,
                reason=f"Iris Ticket renamed by {interaction.user}"
            )
        except discord.Forbidden:
            return await interaction.followup.send(
                "❌ I don't have permission to rename this ticket.",
                ephemeral=True
            )
        except Exception as error:
            print(f"❌ Ticket rename error: {error}")
            return await interaction.followup.send(
                "❌ I couldn't rename this ticket.",
                ephemeral=True
            )

        embed = IrisEmbed.success(
            "✏️ Ticket Renamed",
            (
                f"This ticket was renamed from `{old_name}` "
                f"to `{new_name}` by {interaction.user.mention}."
            )
        )
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        await interaction.followup.send(
            embed=embed,
            ephemeral=True
        )

        # Logging happens after the user has already received the result.
        await send_ticket_log(
            guild,
            config,
            "✏️ Iris Ticket Renamed",
            (
                f"**Old Name:** `#{old_name}`\n"
                f"**New Name:** `#{new_name}`\n"
                f"**Renamed By:** {interaction.user.mention}"
            ),
            success=True
        )

    # ==========================================
    # ATTACHMENT DETECTOR
    # ==========================================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        if message.author.bot:
            return

        channel = message.channel

        if not isinstance(channel, discord.TextChannel):
            return

        topic = channel.topic or ""

        # Only detect uploads in open Iris tickets.
        if not topic.startswith("Iris Ticket |"):
            return

        if not message.attachments:
            return

        lines = []
        for attachment in message.attachments:
            size_mb = attachment.size / (1024 * 1024)
            filename = discord.utils.escape_markdown(attachment.filename)
            lines.append(
                f"📎 [{filename}]({attachment.url}) • {size_mb:.2f} MB"
            )

        embed = IrisEmbed.success(
            "📎 Attachment Received",
            (
                f"Thanks {message.author.mention}! Iris received "
                f"your attachment{'s' if len(lines) != 1 else ''}.\n\n"
                + "\n".join(lines)
            )
        )
        embed.set_footer(text="Iris • Ticket System")
        embed.timestamp = discord.utils.utcnow()

        try:
            await channel.send(embed=embed)
        except Exception as error:
            print(f"⚠️ Could not acknowledge ticket attachment: {error}")

    # ==========================================
    # RESET TICKET SYSTEM
    # ==========================================

    @app_commands.command(
        name="ticketreset",
        description="Reset the ticket number to 0001 and clear Iris ticket logs."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketreset(
        self,
        interaction: discord.Interaction
    ):

        config = await get_ticket_settings(
            interaction.guild.id
        )

        log_channel = None

        if config and config.get("log_channel_id"):
            log_channel = interaction.guild.get_channel(
                config.get("log_channel_id")
            )

        log_text = (
            log_channel.mention
            if log_channel
            else "No ticket log channel is configured"
        )

        embed = IrisEmbed.warning(
            "⚠️ Reset Ticket System?",
            (
                "This will permanently:\n\n"
                "🔢 Reset the ticket counter to **0001**\n"
                f"🗑️ Delete Iris messages from the ticket log channel\n"
                f"📜 **Log Channel:** {log_text}\n\n"
                "**Existing tickets and transcripts will NOT be deleted.**\n\n"
                "Are you sure you want to continue?"
            )
        )

        embed.set_footer(
            text="Iris • Ticket System"
        )

        await interaction.response.send_message(
            embed=embed,
            view=TicketResetConfirmView(
                self.bot,
                interaction.user.id,
                interaction.guild.id
            ),
            ephemeral=True
        )

    # ==========================================
    # TICKET SETUP
    # ==========================================

    @app_commands.command(
        name="ticketsetup",
        description="Set up the server ticket system."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    @app_commands.describe(
        category="Category where tickets will be created.",
        support_role="Role that can access tickets.",
        log_channel="Channel where ticket logs will be sent."
    )
    async def ticketsetup(
        self,
        interaction: discord.Interaction,
        category: discord.CategoryChannel,
        support_role: discord.Role,
        log_channel: discord.TextChannel
    ):

        await set_ticket_settings(
            interaction.guild.id,
            category.id,
            support_role.id,
            log_channel.id
        )

        embed = IrisEmbed.success(
            "🎫 Iris Ticket System Setup",
            (
                "The Iris Ticket system has been "
                "configured successfully.\n\n"
                "Members can now use the button below "
                "to create a private support ticket."
            )
        )

        embed.add_field(
            name="📂 Ticket Category",
            value=category.mention,
            inline=True
        )

        embed.add_field(
            name="🛡️ Support Role",
            value=support_role.mention,
            inline=True
        )

        embed.add_field(
            name="📜 Ticket Logs",
            value=log_channel.mention,
            inline=True
        )

        embed.set_footer(
            text="Iris • Ticket System"
        )

        await interaction.response.send_message(
            embed=embed
        )

        # ==========================================
        # TICKET PANEL
        # ==========================================

        panel_embed = IrisEmbed.success(
            "🎫 Need Help?",
            (
                "Need assistance? Have a question or problem?\n\n"
                "Click **Create Ticket** below to open "
                "a private support ticket.\n\n"
                "🛡️ **Support Team**\n"
                "Our support team will assist you as soon "
                "as possible.\n\n"
                "📌 **Before opening a ticket**\n"
                "Please make sure your question or issue "
                "hasn't already been answered."
            )
        )

        panel_embed.set_footer(
            text="Iris • Support Center"
        )

        await interaction.channel.send(
            embed=panel_embed,
            view=TicketSetupView()
        )

    # ==========================================
    # TICKET STATUS
    # ==========================================

    @app_commands.command(
        name="ticketstatus",
        description="Show the current ticket system configuration."
    )
    @app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def ticketstatus(
        self,
        interaction: discord.Interaction
    ):

        config = await get_ticket_settings(
            interaction.guild.id
        )

        if not config or not config.get("enabled"):

            embed = IrisEmbed.warning(
                "🎫 Iris Ticket System",
                "The ticket system is currently disabled."
            )

            return await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )

        category = interaction.guild.get_channel(
            config.get("category_id")
        )

        support_role = interaction.guild.get_role(
            config.get("support_role_id")
        )

        log_channel = interaction.guild.get_channel(
            config.get("log_channel_id")
        )

        embed = IrisEmbed.success(
            "🎫 Iris Ticket System",
            "The ticket system is currently enabled."
        )

        embed.add_field(
            name="📂 Category",
            value=(
                category.mention
                if category
                else "Channel not found"
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Support Role",
            value=(
                support_role.mention
                if support_role
                else "Role not found"
            ),
            inline=False
        )

        embed.add_field(
            name="📜 Log Channel",
            value=(
                log_channel.mention
                if log_channel
                else "Channel not found"
            ),
            inline=False
        )

        embed.set_footer(
            text="Iris • Ticket System"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


# ==========================================
# SETUP
# ==========================================

async def setup(bot):

    await bot.add_cog(
        Tickets(bot)
    )

    # Persistent views
    bot.add_view(
        TicketSetupView()
    )

    bot.add_view(
        TicketControlView()
    )

    bot.add_view(
        ClosedTicketView()
    )

    print(
        "✅ Tickets COG LOADED"
    )