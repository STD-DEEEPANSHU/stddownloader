import os
import time
import logging
from typing import Dict, Any, Optional
from config import config
from core.helpers import get_media_cache_key, get_platform_info, human_bytes, extract_url
from core.cache import cache_db
from core.userbot import tg_manager
from extractors.youtube import youtube_engine
from extractors.social_userbot import social_userbot_engine

logger = logging.getLogger(__name__)


class DownloadOrchestrator:
    """
    Master Download Orchestrator.
    - Tier 0: 0.1s Instant Return from Telegram Dump Channel & DB Cache.
    - Tier 1: Platform Router (YouTube Meow API or Social Userbot Engine).
    - Tier 2: Universal yt-dlp Automatic Redundancy.
    - Tier 3: Telegram Dump Channel Archival & Cache Persistence.
    """

    async def process(self, raw_input: str, mode: str = "video") -> Dict[str, Any]:
        start_time = time.time()
        url = extract_url(raw_input)
        if not url:
            return {
                "success": False,
                "error": "No valid URL provided.",
                "elapsed": round(time.time() - start_time, 2)
            }

        mode = "audio" if str(mode).lower() in ("audio", "mp3", "sound") else "video"
        cache_key = get_media_cache_key(url, mode)
        platform, emoji = get_platform_info(url)

        # ---------------------------------------------------------
        # TIER 0: 0.1s Instant Cache Check (Dump Channel & DB)
        # ---------------------------------------------------------
        cached = await cache_db.get_cached_media(cache_key)
        if cached and (cached.get("file_id") or (cached.get("direct_url") and os.path.exists(cached.get("direct_url")))):
            elapsed = round(time.time() - start_time, 3)
            logger.info(f"DownloadOrchestrator: ⚡ [0.1s CACHE HIT] '{cache_key}' (in {elapsed}s)")
            return {
                "success": True,
                "cached": True,
                "platform": platform,
                "platform_emoji": emoji,
                "cache_key": cache_key,
                "file_id": cached.get("file_id", ""),
                "dump_msg_id": cached.get("dump_msg_id"),
                "file_type": cached.get("file_type", mode),
                "title": cached.get("title", f"{platform} Media"),
                "duration": cached.get("duration", 0),
                "width": cached.get("width", 0),
                "height": cached.get("height", 0),
                "file_size": cached.get("file_size", 0),
                "file_size_human": human_bytes(cached.get("file_size", 0)),
                "direct_url": cached.get("direct_url", ""),
                "delivery": "instant_dump_cache",
                "elapsed_seconds": elapsed
            }

        # ---------------------------------------------------------
        # TIER 1: Fresh Download Routing
        # ---------------------------------------------------------
        logger.info(f"DownloadOrchestrator: Cache miss for '{cache_key}'. Starting extraction...")
        
        if youtube_engine.is_youtube(url):
            result = await youtube_engine.download(url, mode=mode)
        else:
            result = await social_userbot_engine.download(url, mode=mode)

        if not result or not result.get("success"):
            elapsed = round(time.time() - start_time, 2)
            return {
                "success": False,
                "error": result.get("error", "Download failed across all primary and backup engines."),
                "platform": platform,
                "cache_key": cache_key,
                "elapsed_seconds": elapsed
            }

        file_path = result.get("file_path", "")
        file_size = result.get("file_size", 0)
        if not file_size and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)

        # ---------------------------------------------------------
        # TIER 2: Telegram Dump Channel Archival & Cache Save
        # ---------------------------------------------------------
        file_id = ""
        dump_msg_id = None

        if config.DUMP_CHANNEL and os.path.exists(file_path):
            uploader = tg_manager.bot if tg_manager.is_bot_available() else (tg_manager.userbot if tg_manager.is_userbot_available() else None)
            if uploader:
                try:
                    logger.info(f"DownloadOrchestrator: Archiving to Dump Channel {config.DUMP_CHANNEL}...")
                    caption = (
                        f"🎬 **{result.get('title', platform)}**\n\n"
                        f"• **Platform:** {emoji} {platform}\n"
                        f"• **Size:** {human_bytes(file_size)}\n"
                        f"• **Cache Key:** `{cache_key}`\n"
                        f"• **Engine:** `{result.get('engine', 'auto')}`\n\n"
                        f"⚡ Saved to StdDownloader Cache"
                    )
                    if mode == "audio":
                        dump_msg = await uploader.send_audio(
                            chat_id=config.DUMP_CHANNEL,
                            audio=file_path,
                            caption=caption,
                            duration=result.get("duration", 0),
                            title=result.get("title", "Audio")
                        )
                        file_id = dump_msg.audio.file_id
                    else:
                        dump_msg = await uploader.send_video(
                            chat_id=config.DUMP_CHANNEL,
                            video=file_path,
                            caption=caption,
                            duration=result.get("duration", 0),
                            width=result.get("width", 0),
                            height=result.get("height", 0),
                            supports_streaming=True
                        )
                        file_id = dump_msg.video.file_id

                    dump_msg_id = dump_msg.id
                    logger.info(f"DownloadOrchestrator: ✅ Archived in Dump Channel (msg_id: {dump_msg_id})")
                except Exception as e:
                    logger.warning(f"DownloadOrchestrator: Could not upload to Dump Channel: {e}")

        # Save to database cache for subsequent 0.1s instant hits
        await cache_db.save_cached_media(
            cache_key=cache_key,
            file_id=file_id,
            file_type=mode,
            title=result.get("title", f"{platform} Media"),
            duration=result.get("duration", 0),
            width=result.get("width", 0),
            height=result.get("height", 0),
            file_size=file_size,
            dump_msg_id=dump_msg_id,
            direct_url=file_path
        )

        elapsed = round(time.time() - start_time, 2)
        return {
            "success": True,
            "cached": False,
            "platform": platform,
            "platform_emoji": emoji,
            "cache_key": cache_key,
            "file_id": file_id,
            "dump_msg_id": dump_msg_id,
            "file_path": file_path,
            "file_size": file_size,
            "file_size_human": human_bytes(file_size),
            "title": result.get("title", f"{platform} Media"),
            "duration": result.get("duration", 0),
            "engine": result.get("engine", "unknown"),
            "elapsed_seconds": elapsed
        }


download_orchestrator = DownloadOrchestrator()
