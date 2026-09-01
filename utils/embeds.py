import discord


class IrisEmbed:

    PRIMARY = discord.Color.from_rgb(88, 101, 242)
    SUCCESS = discord.Color.green()
    ERROR = discord.Color.red()
    WARNING = discord.Color.orange()

    @staticmethod
    def default(title: str, description: str = ""):
        embed = discord.Embed(
            title=title,
            description=description,
            color=IrisEmbed.PRIMARY
        )

        embed.set_footer(
            text="Iris Bot • Version 1.0"
        )

        embed.timestamp = discord.utils.utcnow()

        return embed

    @staticmethod
    def success(title: str, description: str = ""):
        embed = discord.Embed(
            title=title,
            description=description,
            color=IrisEmbed.SUCCESS
        )

        embed.set_footer(
            text="Iris Bot • Success"
        )

        embed.timestamp = discord.utils.utcnow()

        return embed

    @staticmethod
    def error(title: str, description: str = ""):
        embed = discord.Embed(
            title=title,
            description=description,
            color=IrisEmbed.ERROR
        )

        embed.set_footer(
            text="Iris Bot • Error"
        )

        embed.timestamp = discord.utils.utcnow()

        return embed

    @staticmethod
    def warning(title: str, description: str = ""):
        embed = discord.Embed(
            title=title,
            description=description,
            color=IrisEmbed.WARNING
        )

        embed.set_footer(
            text="Iris Bot • Warning"
        )

        embed.timestamp = discord.utils.utcnow()

        return embed