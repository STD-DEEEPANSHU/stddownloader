import os
import asyncio
import logging
from typing import Dict, Any, Optional
from config import config
from core.userbot import tg_manager
from core.helpers import get_media_cache_key, get_platform_info

logger = logging.getLogger(__name__)


class SocialUserbotEngine:
    """
    Assistant Userbot Proxy Engine for All Social Media Platforms (Instagram, TikTok, Twitter/X, etc.).
    Queries Telegram helper downloader bots (@DPQbot pool), auto-clicks download buttons, 
    and saves files locally.
    Gracefully falls back to yt-dlp backup if userbot is unconfigured or helper bots timeout.
    """

    async def download(self, url: str, mode: str = "video") -> Dict[str, Any]:
        """Download media using Telegram Assistant UserBot with yt-dlp fallback"""
        
        # Check if Userbot is configured and connected
        if tg_manager.is_userbot_available():
            logger.info("SocialUserbot: Assistant Userbot is active. Querying helper bots pool...")
            result = await self._query_helper_bots(url, mode)
            if result and result.get("success"):
                return result
            logger.warning("SocialUserbot: Helper bots failed or timed out. Falling back to yt-dlp backup...")
        else:
            logger.info("SocialUserbot: Assistant Userbot not active. Routing directly to yt-dlp backup engine...")

        # Fallback to yt-dlp backup engine
        from .ytdlp_engine import ytdlp_engine
        return await ytdlp_engine.download(url, mode=mode)

    async def _query_helper_bots(self, url: str, mode: str) -> Optional[Dict[str, Any]]:
        """Query helper bots pool (@DPQbot etc.), handle inline keyboards, and capture media"""
        ub = tg_manager.userbot
        cache_key = get_media_cache_key(url, mode)
        platform, emoji = get_platform_info(url)
        target_ext = "mp4" if mode == "video" else "mp3"
        dest_file = str(config.DOWNLOAD_DIR / f"{cache_key}.{target_ext}")

        for bot_username in config.HELPER_BOTS:
            try:
                logger.info(f"SocialUserbot: Forwarding '{url}' to helper bot @{bot_username}...")
                
                # Send URL to helper bot
                sent_msg = await ub.send_message(bot_username, url)
                sent_msg_id = sent_msg.id

                # Wait for response messages
                media_msg = None
                deadline = asyncio.get_event_loop().time() + config.USERBOT_TIMEOUT

                while asyncio.get_event_loop().time() < deadline:
                    await asyncio.sleep(2.5)

                    # Get recent messages from helper bot
                    async for msg in ub.get_chat_history(bot_username, limit=4):
                        if msg.id <= sent_msg_id:
                            continue

                        # Check if message contains media
                        if msg.video or msg.audio or msg.document:
                            media_msg = msg
                            break

                        # Check if message has inline keyboard (Quality / Format selection)
                        if msg.reply_markup and getattr(msg.reply_markup, "inline_keyboard", None):
                            clicked = await self._auto_click_button(ub, bot_username, msg, mode)
                            if clicked:
                                await asyncio.sleep(3) # Wait after click

                    if media_msg:
                        break

                if media_msg:
                    logger.info(f"SocialUserbot: Media detected from @{bot_username}! Downloading to disk...")
                    dl_path = await ub.download_media(media_msg, file_name=dest_file)
                    
                    if dl_path and os.path.exists(dl_path) and os.path.getsize(dl_path) > 1000:
                        file_size = os.path.getsize(dl_path)
                        logger.info(f"SocialUserbot: ✅ Download complete! Size: {file_size} bytes")

                        # Purge chat history with helper bot to stay clean
                        try:
                            from pyrogram.raw.functions.messages import DeleteHistory
                            chat_peer = await ub.resolve_peer(bot_username)
                            await ub.invoke(DeleteHistory(peer=chat_peer, max_id=0, revoke=True))
                        except Exception:
                            pass

                        media_obj = media_msg.video or media_msg.audio or media_msg.document
                        title = getattr(media_obj, "file_name", "") or f"{platform} Media"
                        duration = getattr(media_obj, "duration", 0) or 0
                        width = getattr(media_obj, "width", 0) or 0
                        height = getattr(media_obj, "height", 0) or 0

                        return {
                            "success": True,
                            "platform": platform,
                            "title": title,
                            "file_path": str(dl_path),
                            "file_size": file_size,
                            "duration": duration,
                            "width": width,
                            "height": height,
                            "mode": mode,
                            "engine": f"userbot_helper_@{bot_username}"
                        }

            except Exception as e:
                logger.warning(f"SocialUserbot: Error querying helper @{bot_username}: {e}")

        return None

    async def _auto_click_button(self, ub, bot_username: str, msg, mode: str) -> bool:
        """Auto-click the best resolution / format button in inline keyboard"""
        try:
            keywords = ["720", "480", "mp4", "video", "best", "download", "hd"] if mode == "video" else ["mp3", "audio", "music", "320", "128"]
            for row in msg.reply_markup.inline_keyboard:
                for btn in row:
                    btn_text = btn.text.lower()
                    if any(k in btn_text for k in keywords):
                        logger.info(f"SocialUserbot: Clicking button '{btn.text}'...")
                        await msg.click(btn.text)
                        return True
            # If no keyword matches, click first button
            first_btn = msg.reply_markup.inline_keyboard[0][0]
            await msg.click(first_btn.text)
            return True
        except Exception as e:
            logger.warning(f"SocialUserbot: Button click error: {e}")
            return False


social_userbot_engine = SocialUserbotEngine()
