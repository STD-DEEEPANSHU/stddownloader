import sqlite3
import datetime
import asyncio
import logging
from typing import Dict, Any, Optional
from config import config

logger = logging.getLogger(__name__)


class MediaCacheManager:
    """
    High-Performance Media Cache Manager.
    Uses MongoDB (Async Motor) when MONGO_URI is set;
    Gracefully falls back to local SQLite (media_cache.sqlite3) automatically.
    """

    def __init__(self):
        self.use_mongo = False
        self.mongo_client = None
        self.mongo_db = None
        self.sqlite_file = config.BASE_DIR / "media_cache.sqlite3"
        self._initialized = False

    async def init(self):
        """Initialize database connection and schema"""
        if self._initialized:
            return

        if config.MONGO_URI:
            try:
                import motor.motor_asyncio
                self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(
                    config.MONGO_URI,
                    serverSelectionTimeoutMS=4000
                )
                await self.mongo_client.admin.command('ping')
                self.mongo_db = self.mongo_client[config.DB_NAME]
                self.use_mongo = True
                await self.mongo_db.media_cache.create_index("cache_key", unique=True)
                logger.info("MediaCache: Connected successfully to MongoDB.")
                self._initialized = True
                return
            except Exception as e:
                logger.warning(f"MediaCache: MongoDB unreachable ({e}). Falling back to local SQLite.")
                self.use_mongo = False

        # SQLite fallback
        self._init_sqlite()
        self._initialized = True
        logger.info(f"MediaCache: Using local SQLite database ({self.sqlite_file.name}).")

    def _init_sqlite(self):
        """Create media cache table if not exists"""
        with sqlite3.connect(self.sqlite_file) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_cache (
                    cache_key TEXT PRIMARY KEY,
                    file_id TEXT,
                    file_type TEXT DEFAULT 'video',
                    title TEXT DEFAULT '',
                    duration INTEGER DEFAULT 0,
                    width INTEGER DEFAULT 0,
                    height INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    dump_msg_id INTEGER DEFAULT NULL,
                    direct_url TEXT DEFAULT '',
                    created_at TEXT
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_cache_key ON media_cache(cache_key)")
            conn.commit()

    async def get_cached_media(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached Telegram media entry by normalized cache_key for 0.1s delivery"""
        if not cache_key:
            return None

        if not self._initialized:
            await self.init()

        if self.use_mongo:
            try:
                doc = await self.mongo_db.media_cache.find_one({"cache_key": cache_key})
                if doc:
                    doc.pop("_id", None)
                    return doc
            except Exception as e:
                logger.error(f"MediaCache MongoDB read error: {e}")
                return None
        else:
            def _sqlite_get():
                with sqlite3.connect(self.sqlite_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT cache_key, file_id, file_type, title, duration, width, height, file_size, dump_msg_id, direct_url
                        FROM media_cache WHERE cache_key = ?
                    """, (cache_key,))
                    row = cursor.fetchone()
                    if row:
                        return {
                            "cache_key": row[0],
                            "file_id": row[1],
                            "file_type": row[2],
                            "title": row[3],
                            "duration": row[4],
                            "width": row[5],
                            "height": row[6],
                            "file_size": row[7],
                            "dump_msg_id": row[8],
                            "direct_url": row[9]
                        }
                    return None
            return await asyncio.to_thread(_sqlite_get)

    async def save_cached_media(
        self,
        cache_key: str,
        file_id: str = "",
        file_type: str = "video",
        title: str = "",
        duration: int = 0,
        width: int = 0,
        height: int = 0,
        file_size: int = 0,
        dump_msg_id: Optional[int] = None,
        direct_url: str = ""
    ) -> bool:
        """Save media entry into cache for permanent instant re-delivery"""
        if not cache_key:
            return False

        if not self._initialized:
            await self.init()

        now = datetime.datetime.utcnow().isoformat()

        if self.use_mongo:
            try:
                await self.mongo_db.media_cache.update_one(
                    {"cache_key": cache_key},
                    {"$set": {
                        "cache_key": cache_key,
                        "file_id": file_id,
                        "file_type": file_type,
                        "title": title,
                        "duration": duration,
                        "width": width,
                        "height": height,
                        "file_size": file_size,
                        "dump_msg_id": dump_msg_id,
                        "direct_url": direct_url,
                        "created_at": now
                    }},
                    upsert=True
                )
                logger.info(f"MediaCache: [Saved] '{cache_key}' -> Mongo Cache")
                return True
            except Exception as e:
                logger.error(f"MediaCache MongoDB write error: {e}")
                return False
        else:
            def _sqlite_save():
                with sqlite3.connect(self.sqlite_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO media_cache 
                        (cache_key, file_id, file_type, title, duration, width, height, file_size, dump_msg_id, direct_url, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (cache_key, file_id, file_type, title, duration, width, height, file_size, dump_msg_id, direct_url, now))
                    conn.commit()
            await asyncio.to_thread(_sqlite_save)
            logger.info(f"MediaCache: [Saved] '{cache_key}' -> SQLite Cache")
            return True

    async def get_total_cached(self) -> int:
        """Return total count of cached media items"""
        if not self._initialized:
            await self.init()

        if self.use_mongo:
            try:
                return await self.mongo_db.media_cache.count_documents({})
            except Exception:
                return 0
        else:
            def _sqlite_count():
                with sqlite3.connect(self.sqlite_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM media_cache")
                    return cursor.fetchone()[0]
            return await asyncio.to_thread(_sqlite_count)


cache_db = MediaCacheManager()
