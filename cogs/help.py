import discord
from discord.ext import commands

from database.models import get_prefix, set_prefix


class HelpPrefix(commands.Cog):
    """Prefix-based help and per-server prefix configuration."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx: commands.Context, *, topic: str | None = None):
        """Show Iris commands. Use <prefix>help <topic> for a category."""
        prefix = await get_prefix(ctx.guild.id) if ctx.guild else "!"

        commands_by_category = {
            "🎵 Music": ["play", "pause", "resume", "skip", "queue", "nowplaying", "volume", "shuffle", "clear", "stop", "leave"],
            "🛡️ Moderation": [],
            "🎫 Tickets": [],
            "📜 Logging": [],
            "👋 Welcome": [],
            "🔧 Utility": [],
        }

        # Read the currently loaded slash commands so help stays in sync with the bot.
        for command in self.bot.tree.walk_commands():
            module = (getattr(command, "module", "") or "").lower()
            name = command.qualified_name

            if name in commands_by_category["🎵 Music"]:
                continue
            if "moderation" in module:
                commands_by_category["🛡️ Moderation"].append(name)
            elif "ticket" in module:
                commands_by_category["🎫 Tickets"].append(name)
            elif "logging" in module:
                commands_by_category["📜 Logging"].append(name)
            elif "welcome" in module:
                commands_by_category["👋 Welcome"].append(name)
            elif "utility" in module:
                commands_by_category["🔧 Utility"].append(name)

        if topic:
            topic_lower = topic.lower()
            aliases = {
                "music": "🎵 Music",
                "moderation": "🛡️ Moderation",
                "mod": "🛡️ Moderation",
                "tickets": "🎫 Tickets",
                "ticket": "🎫 Tickets",
                "logging": "📜 Logging",
                "logs": "📜 Logging",
                "welcome": "👋 Welcome",
                "utility": "🔧 Utility",
            }
            category = aliases.get(topic_lower)
            if not category:
                return await ctx.send(f"❌ Unknown help category: `{topic}`")

            names = sorted(set(commands_by_category[category]))
            if not names:
                names = ["Use the slash commands shown in Discord's command menu."]

            embed = discord.Embed(
                title=f"Iris • {category}",
                description="\n".join(f"`/{name}`" for name in names),
                color=discord.Color.blurple(),
            )
            embed.set_footer(text=f"Iris • Prefix: {prefix}")
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="🌸 Iris Help",
            description=(
                f"Use `{prefix}help <category>` for a category.\n"
                f"Most Iris commands are available as slash commands (`/`).\n\n"
                f"**Current prefix:** `{prefix}`"
            ),
            color=discord.Color.blurple(),
        )

        for category, names in commands_by_category.items():
            if names:
                value = " • ".join(f"`/{name}`" for name in sorted(set(names))[:15])
                if len(names) > 15:
                    value += f" • +{len(names) - 15} more"
            else:
                value = "Use the `/` command menu in Discord."
            embed.add_field(name=category, value=value, inline=False)

        embed.add_field(
            name="⚙️ Configuration",
            value=f"`{prefix}prefix <new-prefix>` • Change this server's prefix",
            inline=False,
        )
        embed.set_footer(text="Iris Bot")
        await ctx.send(embed=embed)

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.has_guild_permissions(administrator=True)
    async def prefix_command(self, ctx: commands.Context, new_prefix: str | None = None):
        """View or change the server prefix."""
        current = await get_prefix(ctx.guild.id)

        if not new_prefix:
            return await ctx.send(f"⚙️ Current prefix: `{current}`\nUsage: `{current}prefix <new-prefix>`")

        if len(new_prefix) > 5 or any(ch.isspace() for ch in new_prefix):
            return await ctx.send("❌ Prefix must be 1–5 characters and cannot contain spaces.")

        await set_prefix(ctx.guild.id, new_prefix)
        await ctx.send(f"✅ Prefix changed from `{current}` to `{new_prefix}`.")

    @prefix_command.error
    async def prefix_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You need Administrator permission to change the prefix.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command can only be used in a server.")
        else:
            print(f"❌ Prefix command error: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(HelpPrefix(bot))
    print("✅ Help/Prefix COG LOADED")
