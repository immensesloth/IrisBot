import discord
from discord import app_commands
from discord.ext import commands
import wavelink


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        print("🎵 Music COG INITIALIZED")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"🎵 Lavalink node ready: {payload.node}")

    async def get_player(self, interaction: discord.Interaction):
        if interaction.guild is None:
            return None
        player = interaction.guild.voice_client
        return player if isinstance(player, wavelink.Player) else None

    @app_commands.command(name="play", description="Play a song or YouTube URL.")
    @app_commands.describe(query="Song name or YouTube URL.")
    async def play(self, interaction: discord.Interaction, query: str):
        if interaction.guild is None:
            return await interaction.response.send_message(
                "❌ This command can only be used in a server.", ephemeral=True
            )

        member = interaction.user
        if not isinstance(member, discord.Member) or member.voice is None:
            return await interaction.response.send_message(
                "❌ Join a voice channel first.", ephemeral=True
            )

        await interaction.response.defer()

        try:
            player = await self.get_player(interaction)

            if player is None:
                player = await member.voice.channel.connect(cls=wavelink.Player)
            elif player.channel != member.voice.channel:
                await player.move_to(member.voice.channel)

            tracks = await wavelink.Playable.search(query)

            if not tracks:
                return await interaction.followup.send(
                    "❌ I couldn't find anything for that search."
                )

            track = tracks[0]

            if player.playing:
                await player.queue.put_wait(track)
                return await interaction.followup.send(
                    f"➕ Queued **{track.title}**"
                )

            await player.play(track)

            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{track.title}**",
                color=discord.Color.green()
            )
            if track.artwork:
                embed.set_thumbnail(url=track.artwork)

            embed.add_field(
                name="Requested by",
                value=interaction.user.mention,
                inline=True
            )
            embed.set_footer(text="Iris • Music")

            await interaction.followup.send(embed=embed)

        except Exception as error:
            print(f"❌ Music play error: {error}")
            await interaction.followup.send(
                f"❌ I couldn't play that.\n`{error}`"
            )

    @app_commands.command(
        name="pause",
        description="Pause the current song."
    )
    async def pause(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None or player.current is None:
            return await interaction.response.send_message(
                "❌ Nothing is playing right now.",
                ephemeral=True
            )

        if player.paused:
            return await interaction.response.send_message(
                "⏸️ The music is already paused.",
                ephemeral=True
            )

        await player.pause(True)

        await interaction.response.send_message("⏸️ Music paused.")

    @app_commands.command(
        name="resume",
        description="Resume the paused song."
    )
    async def resume(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None or player.current is None:
            return await interaction.response.send_message(
                "❌ Nothing is playing right now.",
                ephemeral=True
            )

        if not player.paused:
            return await interaction.response.send_message(
                "▶️ The music is already playing.",
                ephemeral=True
            )

        await player.pause(False)

        await interaction.response.send_message("▶️ Music resumed.")

    @app_commands.command(
        name="skip",
        description="Skip the current song."
    )
    async def skip(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None or player.current is None:
            return await interaction.response.send_message(
                "❌ Nothing is playing right now.",
                ephemeral=True
            )

        current = player.current
        await player.skip()

        if player.queue:
            await interaction.response.send_message(
                f"⏭️ Skipped **{current.title}**."
            )
        else:
            await interaction.response.send_message(
                f"⏭️ Skipped **{current.title}**. The queue is empty."
            )

    @app_commands.command(
        name="queue",
        description="Show the current music queue."
    )
    async def queue(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't connected to a voice channel.",
                ephemeral=True
            )

        if player.current is None and not player.queue:
            return await interaction.response.send_message(
                "📭 The music queue is empty.",
                ephemeral=True
            )

        lines = []

        if player.current:
            lines.append(
                f"🎵 **Now:** {player.current.title}"
            )

        queued = list(player.queue)

        if queued:
            lines.append("")
            for index, track in enumerate(queued[:10], start=1):
                lines.append(
                    f"`{index}.` {track.title}"
                )

            if len(queued) > 10:
                lines.append(
                    f"\n…and **{len(queued) - 10}** more."
                )
        else:
            lines.append("\n📭 **Up next:** Nothing")

        embed = discord.Embed(
            title="📜 Music Queue",
            description="\n".join(lines),
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f"Iris • {len(queued)} queued")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="nowplaying",
        description="Show the currently playing song."
    )
    async def nowplaying(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None or player.current is None:
            return await interaction.response.send_message(
                "❌ Nothing is playing right now.",
                ephemeral=True
            )

        track = player.current

        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{track.title}**",
            color=discord.Color.green()
        )

        if track.artwork:
            embed.set_thumbnail(url=track.artwork)

        status = "⏸️ Paused" if player.paused else "▶️ Playing"

        embed.add_field(
            name="Status",
            value=status,
            inline=True
        )
        embed.add_field(
            name="Volume",
            value=f"{player.volume}%",
            inline=True
        )
        embed.add_field(
            name="Queue",
            value=f"{len(player.queue)} song(s)",
            inline=True
        )

        embed.set_footer(text="Iris • Music")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="volume",
        description="Set the music volume."
    )
    @app_commands.describe(
        level="Volume from 0 to 1000."
    )
    async def volume(
        self,
        interaction: discord.Interaction,
        level: app_commands.Range[int, 0, 1000]
    ):
        player = await self.get_player(interaction)

        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't connected to a voice channel.",
                ephemeral=True
            )

        await player.set_volume(level)

        await interaction.response.send_message(
            f"🔊 Volume set to **{level}%**."
        )

    @app_commands.command(
        name="shuffle",
        description="Shuffle the music queue."
    )
    async def shuffle(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't connected to a voice channel.",
                ephemeral=True
            )

        if len(player.queue) < 2:
            return await interaction.response.send_message(
                "❌ I need at least 2 queued songs to shuffle.",
                ephemeral=True
            )

        player.queue.shuffle()

        await interaction.response.send_message(
            "🔀 Queue shuffled."
        )

    @app_commands.command(
        name="clear",
        description="Clear all queued songs."
    )
    async def clear(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)

        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't connected to a voice channel.",
                ephemeral=True
            )

        count = len(player.queue)

        if count == 0:
            return await interaction.response.send_message(
                "📭 The queue is already empty.",
                ephemeral=True
            )

        player.queue.clear()

        await interaction.response.send_message(
            f"🧹 Cleared **{count}** queued song(s)."
        )

    @app_commands.command(name="stop", description="Stop the current music.")
    async def stop(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't playing music right now.", ephemeral=True
            )

        await player.stop()
        await interaction.response.send_message("⏹️ Music stopped.")

    @app_commands.command(name="leave", description="Disconnect Iris from voice.")
    async def leave(self, interaction: discord.Interaction):
        player = await self.get_player(interaction)
        if player is None:
            return await interaction.response.send_message(
                "❌ Iris isn't connected to a voice channel.", ephemeral=True
            )

        await player.disconnect()
        await interaction.response.send_message(
            "👋 Disconnected from the voice channel."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
    print("✅ Music COG LOADED")
