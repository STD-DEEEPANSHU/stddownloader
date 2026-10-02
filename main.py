import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from config import config
from core.cache import cache_db
from core.userbot import tg_manager
from core.helpers import get_media_cache_key, get_platform_info, human_bytes
from services.download_service import download_orchestrator

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s : %(message)s"
)
logger = logging.getLogger("stddownloader")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing StdDownloader Engine...")
    await cache_db.init()
    await tg_manager.init()
    total_cached = await cache_db.get_total_cached()
    logger.info(f"StdDownloader Ready! ({total_cached} media items currently in cache)")
    yield
    # Shutdown
    logger.info("Shutting down StdDownloader Engine...")
    await tg_manager.close()


app = FastAPI(
    title="⚡ StdDownloader API",
    description="Dual-Engine High Speed Social Media & YouTube Downloader Microservice by STD DEEPANSHU",
    version=config.VERSION,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DownloadRequest(BaseModel):
    url: str = Field(..., description="Target media URL (YouTube, Instagram, TikTok, Twitter/X, etc.)")
    mode: str = Field("video", description="Extraction mode: 'video' (MP4) or 'audio' (MP3)")


@app.get("/", tags=["General"])
async def root():
    total_cached = await cache_db.get_total_cached()
    return {
        "service": "StdDownloader Engine",
        "author": "STD DEEPANSHU",
        "network": "TeamStdNetwork",
        "version": config.VERSION,
        "status": "online",
        "architecture": {
            "tier_0": "0.1s Dump Channel & DB Cache",
            "tier_1_youtube": "Meow/Yuki API Direct Stream (/stream/{id})",
            "tier_1_social": f"Telegram Assistant Userbot (@{config.HELPER_BOTS[0]} pool)",
            "backup_engine": "yt-dlp with mobile client spoofing (android/ios)"
        },
        "dump_channel": config.DUMP_CHANNEL,
        "total_cached_items": total_cached,
        "userbot_active": tg_manager.is_userbot_available(),
        "docs_url": "/docs"
    }


@app.get("/health", tags=["General"])
async def health():
    return {"status": "ok", "version": config.VERSION}


@app.get("/api/download", tags=["Downloader"])
async def download_get(
    url: str = Query(..., description="Direct social media or YouTube link"),
    mode: str = Query("video", description="Mode: 'video' or 'audio'")
):
    """Download media from any platform with automated caching and fallback"""
    res = await download_orchestrator.process(url, mode=mode)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res


@app.post("/api/download", tags=["Downloader"])
async def download_post(payload: DownloadRequest = Body(...)):
    """JSON API download endpoint"""
    res = await download_orchestrator.process(payload.url, mode=payload.mode)
    if not res.get("success"):
        return JSONResponse(status_code=400, content=res)
    return res


@app.get("/api/cache/check", tags=["Cache"])
async def check_cache(
    url: str = Query(..., description="URL to check in instant cache"),
    mode: str = Query("video", description="Extraction mode")
):
    """Check if URL already exists in 0.1s Dump Cache without triggering download"""
    cache_key = get_media_cache_key(url, mode)
    platform, emoji = get_platform_info(url)
    cached = await cache_db.get_cached_media(cache_key)

    if cached:
        return {
            "found": True,
            "cache_key": cache_key,
            "platform": platform,
            "platform_emoji": emoji,
            "file_id": cached.get("file_id"),
            "dump_msg_id": cached.get("dump_msg_id"),
            "file_size": cached.get("file_size"),
            "file_size_human": human_bytes(cached.get("file_size", 0)),
            "title": cached.get("title")
        }
    return {
        "found": False,
        "cache_key": cache_key,
        "platform": platform,
        "message": "URL not cached yet. Ready for fresh extraction."
    }


@app.get("/api/files/{filename}", tags=["Storage"])
async def serve_file(filename: str):
    """Serve downloaded media files directly from local storage"""
    file_path = config.DOWNLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested media file not found.")
    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=filename
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
