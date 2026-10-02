import os
import re
import asyncio
import logging
import aiohttp
from typing import Optional, Dict, Any, Tuple
from config import config
from core.helpers import extract_youtube_id

logger = logging.getLogger(__name__)


class YouTubeEngine:
    """
    Dedicated YouTube Engine.
    Primary: Meow / Yuki API high-speed direct stream extraction.
    Backup: yt-dlp with mobile client spoofing & lossless audio extraction.
    """

    @staticmethod
    def is_youtube(url: str) -> bool:
        if not url:
            return False
        u = str(url).lower()
        return "youtube.com" in u or "youtu.be" in u

    async def download(self, url: str, mode: str = "video") -> Dict[str, Any]:
        """
        Download YouTube media.
        mode: 'video' (MP4) or 'audio' (320kbps MP3)
        """
        video_id = extract_youtube_id(url)
        if not video_id:
            return {
                "success": False,
                "error": f"Invalid YouTube URL format: {url}"
            }

        ext = "mp4" if mode == "video" else "mp3"
        file_path = str(config.DOWNLOAD_DIR / f"yt_{video_id}_{mode}.{ext}")

        # Check local disk cache first
        if os.path.exists(file_path) and os.path.getsize(file_path) > 10000:
            logger.info(f"YouTubeEngine: [Local Disk Hit] {file_path}")
            return {
                "success": True,
                "platform": "YouTube",
                "video_id": video_id,
                "title": f"YouTube {mode.capitalize()} - {video_id}",
                "file_path": file_path,
                "mode": mode,
                "engine": "local_disk_cache"
            }

        # Step 1: Try Primary Meow / Yuki API
        api_result = await self._download_via_meow_api(video_id, mode, file_path)
        if api_result and api_result.get("success"):
            return api_result

        # Step 2: Fallback to yt-dlp Backup Engine
        logger.warning(f"YouTubeEngine: Meow API failed for {video_id}. Triggering yt-dlp backup...")
        from .ytdlp_engine import ytdlp_engine
        return await ytdlp_engine.download(f"https://www.youtube.com/watch?v={video_id}", mode=mode)

    async def _download_via_meow_api(
        self, 
        video_id: str, 
        mode: str, 
        output_path: str
    ) -> Optional[Dict[str, Any]]:
        """Download stream chunks via Meow/Yuki API"""
        api_url = config.MEOW_API_URL
        api_key = config.MEOW_API_KEY

        qualities = ["720", "480", "360"] if mode == "video" else ["320", "192", "128"]
        media_type = "video" if mode == "video" else "audio"

        for q in qualities:
            stream_url = f"{api_url}/stream/{video_id}?key={api_key}&type={media_type}&quality={q}"
            logger.info(f"YouTubeEngine: Trying Meow API for {video_id} (quality={q})...")

            try:
                timeout = aiohttp.ClientTimeout(total=180)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(stream_url) as resp:
                        if resp.status == 200:
                            content_type = resp.headers.get("Content-Type", "").lower()
                            # If video is requested, ensure response is actually a video stream (not audio/webm or audio/opus)
                            if mode == "video" and "video" not in content_type:
                                logger.warning(
                                    f"YouTubeEngine: Meow API returned audio stream '{content_type}' instead of video for {video_id}. "
                                    f"Skipping to yt-dlp backup for full HD video track."
                                )
                                continue

                            with open(output_path, "wb") as f:
                                async for chunk in resp.content.iter_chunked(131072):
                                    f.write(chunk)

                            if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                                fsize = os.path.getsize(output_path)
                                logger.info(f"YouTubeEngine: ✅ Meow API SUCCESS ({q})! Size: {fsize} bytes")
                                return {
                                    "success": True,
                                    "platform": "YouTube",
                                    "video_id": video_id,
                                    "title": f"YouTube {media_type.capitalize()} {q}p",
                                    "file_path": output_path,
                                    "mode": mode,
                                    "quality": q,
                                    "engine": "meow_api"
                                }
                            else:
                                if os.path.exists(output_path):
                                    os.remove(output_path)
                        else:
                            logger.warning(f"YouTubeEngine: Meow API returned HTTP {resp.status} for quality {q}")
            except Exception as e:
                logger.warning(f"YouTubeEngine: Meow API error for {video_id} ({q}): {e}")

        return None


youtube_engine = YouTubeEngine()
