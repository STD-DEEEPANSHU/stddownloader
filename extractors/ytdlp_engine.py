import os
import asyncio
import logging
from typing import Dict, Any, Optional
from config import config
from core.helpers import get_media_cache_key, get_platform_info

logger = logging.getLogger(__name__)


class YtDlpBackupEngine:
    """
    High-Reliability yt-dlp Backup Engine.
    Used for YouTube fallback and direct extraction of any social media URL.
    Employs mobile client spoofing (android/ios) to prevent IP throttling & 403 blocks.
    """

    async def download(self, url: str, mode: str = "video") -> Dict[str, Any]:
        """Download URL using yt-dlp asynchronous worker"""
        return await asyncio.to_thread(self._sync_download, url, mode)

    def _sync_download(self, url: str, mode: str = "video") -> Dict[str, Any]:
        try:
            import yt_dlp
        except ImportError:
            return {
                "success": False,
                "error": "yt-dlp is not installed in the python environment."
            }

        cache_key = get_media_cache_key(url, mode)
        platform, emoji = get_platform_info(url)
        ext = "mp4" if mode == "video" else "mp3"
        output_template = str(config.DOWNLOAD_DIR / f"{cache_key}.%(ext)s")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "socket_timeout": 30,
            "max_filesize": config.MAX_FILE_SIZE,
            "extractor_retries": 3,
            "ignoreerrors": False,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        }

        # Mobile client spoofing for YouTube to bypass bot detection
        if "youtube.com" in url.lower() or "youtu.be" in url.lower():
            ydl_opts["extractor_args"] = {
                "youtube": {
                    "player_client": ["android", "ios", "web_embedded"]
                }
            }

        if mode == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "320",
                }],
            })
        else:
            # Video mode: best MP4 or muxed video+audio
            ydl_opts.update({
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
            })

        logger.info(f"YtDlpBackupEngine: Starting extraction for '{url}' (mode={mode})...")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    return {"success": False, "error": "yt-dlp could not extract media info."}

                # Find generated file
                expected_file = str(config.DOWNLOAD_DIR / f"{cache_key}.{ext}")
                final_file = expected_file

                if not os.path.exists(expected_file):
                    # Check if saved with different extension or original ext
                    for f in os.listdir(config.DOWNLOAD_DIR):
                        if f.startswith(cache_key):
                            final_file = str(config.DOWNLOAD_DIR / f)
                            break

                if not os.path.exists(final_file) or os.path.getsize(final_file) < 1000:
                    return {
                        "success": False,
                        "error": "yt-dlp completed download but output file is missing or empty."
                    }

                title = info.get("title", f"{platform} Media")
                duration = int(info.get("duration", 0) or 0)
                width = int(info.get("width", 0) or 0)
                height = int(info.get("height", 0) or 0)
                thumbnail = info.get("thumbnail", "")
                file_size = os.path.getsize(final_file)

                logger.info(f"YtDlpBackupEngine: ✅ SUCCESS! Saved '{final_file}' ({file_size} bytes)")

                return {
                    "success": True,
                    "platform": platform,
                    "title": title,
                    "file_path": final_file,
                    "file_size": file_size,
                    "duration": duration,
                    "width": width,
                    "height": height,
                    "thumbnail": thumbnail,
                    "mode": mode,
                    "engine": "yt_dlp_backup"
                }
        except Exception as e:
            logger.error(f"YtDlpBackupEngine error for '{url}': {e}")
            return {
                "success": False,
                "error": f"yt-dlp error: {str(e)}"
            }


ytdlp_engine = YtDlpBackupEngine()
