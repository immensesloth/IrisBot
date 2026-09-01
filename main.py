import os
import asyncio
import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv

from database.database import connect_database
from database.models import get_prefix

# ==========================
# LOAD ENVIRONMENT VARIABLES
# ==========================

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# ==========================
# BOT INTENTS
# ==========================

intents = discord.Intents.default()

intents.messages = True
intents.message_content = True
intents.members = True
intents.guilds = True

# ==========================
# CREATE BOT
# ==========================

async def get_bot_prefix(bot, message):
    if message.guild is None:
        return "!"
    return await get_prefix(message.guild.id)


bot = commands.Bot(
    command_prefix=get_bot_prefix,
    intents=intents,
    help_command=None
)

bot.start_time = discord.utils.utcnow()

# ==========================
# WAVELINK / LAVALINK
# ==========================

@bot.event
async def setup_hook():
    try:
        node = wavelink.Node(
            uri="http://127.0.0.1:2333",
            password="iris"
        )
        await wavelink.Pool.connect(
            nodes=[node],
            client=bot
        )
        print("🎵 Connected to Lavalink")
    except Exception as e:
        print(f"❌ Failed to connect to Lavalink: {e}")

# ==========================
# READY EVENT
# ==========================

@bot.event
async def on_ready():

    print("=" * 50)
    print(f"Logged in as {bot.user}")
    print(f"Bot ID: {bot.user.id}")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"Sync Error: {e}")

    print("=" * 50)

# ==========================
# LOAD COGS
# ==========================

async def load_cogs():

    cogs = [
        "cogs.help",
        "cogs.utility",
        "cogs.moderation",
        "cogs.logging",
        "cogs.welcome",
        "cogs.tickets",
        "cogs.music"
    ]

    for cog in cogs:
        try:
            await bot.load_extension(cog)
            print(f"✅ Loaded {cog}")
        except Exception as e:
            print(f"❌ Failed to load {cog}")
            print(e)

# ==========================
# MAIN
# ==========================

async def main():

    async with bot:

        # Connect MongoDB
        await connect_database()

        # Load Extensions
        await load_cogs()

        # Start Bot
        await bot.start(TOKEN)

# ==========================
# START PROGRAM
# ==========================

if __name__ == "__main__":
    asyncio.run(main())