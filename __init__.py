"""
⚡ StdDownloader Engine
Dual-Engine High Speed Social Media & YouTube Downloader Microservice
Developed by STD DEEPANSHU | TeamStdNetwork
"""

from .config import config
from .services.download_service import download_orchestrator
from .core.cache import cache_db
from .core.helpers import get_media_cache_key, get_platform_info

__version__ = "2.0.0"
__all__ = ["config", "download_orchestrator", "cache_db", "get_media_cache_key", "get_platform_info"]
