import logging
from typing import Optional, Any
from config import config

logger = logging.getLogger(__name__)

# Try to import pyrofork / pyrogram / hydrogram
Client = None
try:
    from pyrogram import Client
except ImportError:
    try:
        from pyrofork import Client
    except ImportError:
        try:
            from hydrogram import Client
        except ImportError:
            Client = None

userbot: Optional[Any] = None
bot_client: Optional[Any] = None

class TelegramManager:
    """Manages Telegram Assistant Userbot and Bot Client instances"""
    
    def __init__(self):
        self.userbot = None
        self.bot = None
        self.is_userbot_ready = False
        self.is_bot_ready = False

    async def init(self):
        """Start Telegram Assistant Userbot if STRING_SESSION is configured"""
        if not Client:
            logger.warning("TelegramManager: No Pyrogram/Pyrofork library installed.")
            return

        # 1. Assistant Userbot (String Session)
        if config.STRING_SESSION and config.API_ID and config.API_HASH:
            try:
                self.userbot = Client(
                    name="std_assistant_userbot",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    session_string=config.STRING_SESSION,
                    in_memory=True
                )
                await self.userbot.start()
                self.is_userbot_ready = True
                try:
                    me = await self.userbot.get_me()
                    username = getattr(me, "username", None) or getattr(me, "id", "User")
                    logger.info(f"TelegramManager: Assistant Userbot connected as @{username}")
                except Exception as ex:
                    logger.info(f"TelegramManager: Assistant Userbot connected (metadata bypassed: {ex})")
            except Exception as e:
                logger.warning(f"TelegramManager: Failed to start Assistant Userbot: {e}")
                self.is_userbot_ready = False

        # 2. Main Bot Client (if BOT_TOKEN is configured)
        if config.BOT_TOKEN and config.API_ID and config.API_HASH:
            try:
                self.bot = Client(
                    name="std_downloader_bot",
                    api_id=config.API_ID,
                    api_hash=config.API_HASH,
                    bot_token=config.BOT_TOKEN,
                    in_memory=True
                )
                await self.bot.start()
                self.is_bot_ready = True
                me_bot = await self.bot.get_me()
                logger.info(f"TelegramManager: Bot client connected as @{me_bot.username}")
            except Exception as e:
                logger.warning(f"TelegramManager: Failed to start Bot Client: {e}")
                self.is_bot_ready = False

    def is_userbot_available(self) -> bool:
        """Check if assistant userbot is alive and connected"""
        return self.is_userbot_ready and self.userbot is not None and getattr(self.userbot, "is_connected", False)

    def is_bot_available(self) -> bool:
        """Check if bot client is connected"""
        return self.is_bot_ready and self.bot is not None and getattr(self.bot, "is_connected", False)

    async def close(self):
        """Gracefully disconnect clients"""
        if self.userbot and getattr(self.userbot, "is_connected", False):
            await self.userbot.stop()
        if self.bot and getattr(self.bot, "is_connected", False):
            await self.bot.stop()


tg_manager = TelegramManager()
