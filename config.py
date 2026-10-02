import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()


class Config:
    """Central Configuration for StdDownloader Engine"""
    
    PROJECT_NAME: str = "StdDownloader Engine"
    VERSION: str = "2.0.0"
    AUTHOR: str = "STD DEEPANSHU"
    NETWORK: str = "TeamStdNetwork"

    # Base Directories
    BASE_DIR = Path(__file__).resolve().parent
    DOWNLOAD_DIR = BASE_DIR / "downloads"
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Telegram API Credentials (Optional, needed for UserBot Assistant & Dump Channel)
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")

    # Assistant Userbot (String Session) for querying helper downloader bots
    STRING_SESSION = os.getenv("STRING_SESSION", "").strip()

    # Third-Party Helper Bots Pool (Default: @DPQbot)
    HELPER_BOTS = [
        b.strip().lstrip("@") 
        for b in os.getenv("HELPER_BOTS", "DPQbot").split(",") 
        if b.strip()
    ]

    # Permanent Media Dump & Cache Channel (For 0.1s instant re-delivery)
    DUMP_CHANNEL_RAW = os.getenv("DUMP_CHANNEL", "-1004458588038").strip()
    try:
        DUMP_CHANNEL = int(DUMP_CHANNEL_RAW)
    except ValueError:
        DUMP_CHANNEL = DUMP_CHANNEL_RAW

    # YouTube Meow / Yuki API Stream Engine
    MEOW_API_URL = os.getenv("MEOW_API_URL", "https://music.yukiapi.site").rstrip("/")
    MEOW_API_KEY = os.getenv("MEOW_API_KEY", "yuki_feabaea9d68d372ee341424466c8d0ef").strip()

    # Database Configuration (MongoDB or Local SQLite fallback)
    MONGO_URI = (
        os.getenv("MONGO_URI") 
        or os.getenv("MONGO_URL") 
        or os.getenv("MONGODB_URI") 
        or ""
    ).strip()
    DB_NAME = os.getenv("DB_NAME", "stddownloader").strip()

    # Limits & Timeouts
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(2 * 1024 * 1024 * 1024))) # 2 GB
    USERBOT_TIMEOUT = int(os.getenv("USERBOT_TIMEOUT", "40")) # seconds


config = Config()
