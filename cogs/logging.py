from .logging_parts.core import LoggingCore
from .logging_parts.messages import MessageLogging
from .logging_parts.members import MemberLogging
from .logging_parts.roles import RoleLogging
from .logging_parts.channels import ChannelLogging
from .logging_parts.voice import VoiceLogging
from .logging_parts.server import ServerLogging
from .logging_parts.threads import ThreadLogging
from .logging_parts.emojis import EmojiStickerLogging


async def setup(bot):
    await bot.add_cog(LoggingCore(bot))

    message_cog = MessageLogging(bot)
    await bot.add_cog(message_cog)

    bot.add_listener(
        message_cog.on_raw_message_delete,
        "on_raw_message_delete"
    )

    print("🔥 RAW DELETE LISTENER MANUALLY REGISTERED")

    await bot.add_cog(MemberLogging(bot))
    await bot.add_cog(RoleLogging(bot))
    await bot.add_cog(ChannelLogging(bot))
    await bot.add_cog(VoiceLogging(bot))
    await bot.add_cog(ServerLogging(bot))
    await bot.add_cog(ThreadLogging(bot))
    await bot.add_cog(EmojiStickerLogging(bot))
