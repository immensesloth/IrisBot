from database.database import warnings, settings


# ==========================================
# WARNINGS
# ==========================================

async def add_warning(guild_id, user_id, moderator_id, reason):
    await warnings.insert_one({
        "guild_id": guild_id,
        "user_id": user_id,
        "moderator_id": moderator_id,
        "reason": reason
    })


async def get_warnings(guild_id, user_id):
    return await warnings.find({
        "guild_id": guild_id,
        "user_id": user_id
    }).to_list(length=None)


async def clear_warnings(guild_id, user_id):
    await warnings.delete_many({
        "guild_id": guild_id,
        "user_id": user_id
    })


# ==========================================
# LOG CHANNEL SETTINGS
# ==========================================

LOG_CATEGORIES = [
    "mod",
    "message",
    "member",
    "role",
    "channel",
    "voice",
    "server",
    "thread",
    "emoji"
]


# ==========================================
# SET LOG CHANNEL
# ==========================================

async def set_log_channel(
    guild_id,
    channel_id,
    category=None
):
    """
    Save a log channel.

    category=None:
        Keeps compatibility with the old single log channel.

    category="mod":
        Saves the moderation log channel.

    category="message":
        Saves the message log channel.
    """

    if category is None:
        await settings.update_one(
            {"guild_id": guild_id},
            {
                "$set": {
                    "log_channel": channel_id
                }
            },
            upsert=True
        )
        return

    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                f"log_channels.{category}": channel_id
            }
        },
        upsert=True
    )


# ==========================================
# GET LOG CHANNEL
# ==========================================

async def get_log_channel(
    guild_id,
    category=None
):
    """
    Get a log channel.

    category=None:
        Returns the old single log channel.

    category="mod":
        Returns the moderation log channel.
    """

    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    # Old single-channel system
    if category is None:
        return data.get("log_channel")

    # New multi-channel system
    log_channels = data.get(
        "log_channels",
        {}
    )

    return log_channels.get(category)


# ==========================================
# REMOVE LOG CHANNEL
# ==========================================

async def remove_log_channel(
    guild_id,
    category=None
):
    """
    Remove a log channel.

    category=None:
        Removes the old single log channel.

    category="mod":
        Removes only the moderation log channel.
    """

    if category is None:
        await settings.update_one(
            {"guild_id": guild_id},
            {
                "$unset": {
                    "log_channel": ""
                }
            }
        )
        return

    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$unset": {
                f"log_channels.{category}": ""
            }
        }
    )


# ==========================================
# GET ALL LOG CHANNELS
# ==========================================

async def get_all_log_channels(guild_id):
    """
    Returns all configured log channels.
    """

    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return {}

    return data.get(
        "log_channels",
        {}
    )


# ==========================================
# SET ALL LOG CHANNELS
# ==========================================

async def set_all_log_channels(
    guild_id,
    channels
):
    """
    Save all log channels at once.

    Example:

    {
        "mod": 123456,
        "message": 234567,
        "member": 345678
    }
    """

    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                "log_channels": channels
            }
        },
        upsert=True
    )


# ==========================================
# REMOVE ALL LOG CHANNELS
# ==========================================

async def remove_all_log_channels(guild_id):

    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$unset": {
                "log_channels": ""
            }
        }
    )

# ==========================================
# WELCOME / GOODBYE SETTINGS
# ==========================================

async def set_welcome_channel(guild_id, channel_id):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                "welcome.channel_id": channel_id,
                "welcome.enabled": True
            }
        },
        upsert=True
    )


async def get_welcome_settings(guild_id):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    return data.get("welcome")


async def remove_welcome(guild_id):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$unset": {
                "welcome": ""
            }
        }
    )


async def set_goodbye_channel(guild_id, channel_id):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                "goodbye.channel_id": channel_id,
                "goodbye.enabled": True
            }
        },
        upsert=True
    )


async def get_goodbye_settings(guild_id):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    return data.get("goodbye")


async def remove_goodbye(guild_id):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$unset": {
                "goodbye": ""
            }
        }
    )

# ==========================================
# TICKET SETTINGS
# ==========================================

async def set_ticket_settings(
    guild_id,
    category_id,
    support_role_id=None,
    log_channel_id=None
):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                "tickets.category_id": category_id,
                "tickets.support_role_id": support_role_id,
                "tickets.log_channel_id": log_channel_id,
                "tickets.enabled": True
            }
        },
        upsert=True
    )


async def get_ticket_settings(guild_id):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    return data.get("tickets")


async def remove_ticket_settings(guild_id):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$unset": {
                "tickets": ""
            }
        }
    )


# ==========================================
# OPEN TICKETS
# ==========================================

async def create_ticket(
    guild_id,
    channel_id,
    user_id,
    reason=None
):
    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                f"tickets.open.{channel_id}": {
                    "channel_id": channel_id,
                    "user_id": user_id,
                    "reason": reason,
                    "status": "open"
                }
            }
        },
        upsert=True
    )


async def get_ticket(
    guild_id,
    channel_id
):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    tickets = data.get(
        "tickets",
        {}
    )

    open_tickets = tickets.get(
        "open",
        {}
    )

    return open_tickets.get(
        str(channel_id)
    ) or open_tickets.get(
        channel_id
    )


async def close_ticket(
    guild_id,
    channel_id
):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return

    tickets = data.get(
        "tickets",
        {}
    )

    open_tickets = tickets.get(
        "open",
        {}
    )

    ticket = (
        open_tickets.get(str(channel_id))
        or open_tickets.get(channel_id)
    )

    if not ticket:
        return

    await settings.update_one(
        {"guild_id": guild_id},
        {
            "$set": {
                f"tickets.closed.{channel_id}": {
                    **ticket,
                    "status": "closed"
                }
            },
            "$unset": {
                f"tickets.open.{channel_id}": ""
            }
        }
    )


async def get_user_open_ticket(
    guild_id,
    user_id
):
    data = await settings.find_one(
        {"guild_id": guild_id}
    )

    if not data:
        return None

    tickets = data.get(
        "tickets",
        {}
    )

    open_tickets = tickets.get(
        "open",
        {}
    )

    for ticket in open_tickets.values():
        if ticket.get("user_id") == user_id:
            return ticket

    return None        
# ==========================================
# PREFIX SETTINGS
# ==========================================

DEFAULT_PREFIX = "!"


async def get_prefix(guild_id):
    """Return the configured prefix for a guild, or the default prefix."""
    if not guild_id:
        return DEFAULT_PREFIX

    data = await settings.find_one({"guild_id": guild_id})
    if not data:
        return DEFAULT_PREFIX

    prefix = data.get("prefix", DEFAULT_PREFIX)
    return prefix if isinstance(prefix, str) and prefix else DEFAULT_PREFIX


async def set_prefix(guild_id, prefix):
    """Persist a guild-specific prefix in MongoDB."""
    await settings.update_one(
        {"guild_id": guild_id},
        {"$set": {"prefix": prefix}},
        upsert=True
    )
