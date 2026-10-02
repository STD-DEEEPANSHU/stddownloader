import re
import hashlib
from typing import Optional, Tuple
from urllib.parse import urlparse


def extract_youtube_id(link: str) -> Optional[str]:
    """Extract clean 11-char YouTube video ID from any link format (shorts, youtu.be, watch?v=)"""
    if not link:
        return None
    link = str(link).strip()
    if len(link) == 11 and re.match(r"^[0-9A-Za-z_-]{11}$", link):
        return link
    patterns = [
        r"(?:v=|\/embed\/|\/v\/|\/shorts\/)([0-9A-Za-z_-]{11})",
        r"youtu\.be\/([0-9A-Za-z_-]{11})",
        r"youtube\.com\/watch\?.*v=([0-9A-Za-z_-]{11})"
    ]
    for p in patterns:
        m = re.search(p, link)
        if m:
            return m.group(1)
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    return link.split("/")[-1].split("?")[0]


def get_media_cache_key(url: str, mode: str = "video") -> str:
    """
    Extract a normalized, unique media identifier from URL across platforms.
    Returns keys like:
    - YouTube video / shorts: 'yt_dQw4w9WgXcQ_video'
    - Instagram reel / post: 'ig_C8xY9zABCDE_video'
    - TikTok video: 'tt_728491029182_video'
    - Twitter / X: 'x_1782910281_video'
    - Facebook: 'fb_1029384819_video'
    - Pinterest: 'pin_123456789_video'
    - Generic fallback: 'gen_<md5>_video'
    """
    if not url:
        return f"gen_unknown_{mode}"

    u = str(url).strip()

    # 1. YouTube
    if any(d in u for d in ("youtube.com", "youtu.be")):
        yt_id = extract_youtube_id(u)
        if yt_id:
            return f"yt_{yt_id}_{mode}"

    # 2. Instagram (reel, reels, p, tv, stories)
    if any(d in u for d in ("instagram.com", "instagr.am")):
        ig_m = re.search(r"(?:reel|reels|p|tv|stories\/[^\/]+)\/([A-Za-z0-9_-]+)", u)
        if ig_m:
            return f"ig_{ig_m.group(1)}_{mode}"

    # 3. TikTok
    if "tiktok.com" in u:
        tt_m = re.search(r"video\/(\d+)", u)
        if tt_m:
            return f"tt_{tt_m.group(1)}_{mode}"
        # short links (vm.tiktok.com or vt.tiktok.com)
        tt_short = re.search(r"(?:vm|vt)\.tiktok\.com\/([A-Za-z0-9]+)", u)
        if tt_short:
            return f"tt_{tt_short.group(1)}_{mode}"

    # 4. Twitter / X
    if any(d in u for d in ("twitter.com", "x.com")):
        tw_m = re.search(r"status\/(\d+)", u)
        if tw_m:
            return f"x_{tw_m.group(1)}_{mode}"

    # 5. Facebook
    if any(d in u for d in ("facebook.com", "fb.watch", "fb.com")):
        fb_m = re.search(r"(?:videos|reel|watch\?v=)\/(\d+)", u) or re.search(r"v=(\d+)", u)
        if fb_m:
            return f"fb_{fb_m.group(1)}_{mode}"

    # 6. Pinterest
    if any(d in u for d in ("pinterest.com", "pin.it")):
        pin_m = re.search(r"pin\/(\d+)", u) or re.search(r"pin\.it\/([A-Za-z0-9]+)", u)
        if pin_m:
            return f"pin_{pin_m.group(1)}_{mode}"

    # 7. Generic Fallback: Clean URL without tracking parameters + MD5
    parsed = urlparse(u)
    clean_url = f"{parsed.netloc}{parsed.path}".rstrip("/")
    url_hash = hashlib.md5(clean_url.encode("utf-8")).hexdigest()[:16]
    return f"gen_{url_hash}_{mode}"


def get_platform_info(url: str) -> Tuple[str, str]:
    """Return platform name and emoji icon from URL"""
    u = str(url).lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube", "🔴"
    if "instagram.com" in u or "instagr.am" in u:
        return "Instagram", "🟣"
    if "tiktok.com" in u:
        return "TikTok", "🩵"
    if "twitter.com" in u or "x.com" in u:
        return "Twitter / X", "⚪"
    if "pinterest.com" in u or "pin.it" in u:
        return "Pinterest", "📌"
    if "facebook.com" in u or "fb.watch" in u:
        return "Facebook", "🔵"
    if "reddit.com" in u or "redd.it" in u:
        return "Reddit", "🟠"
    if "spotify.com" in u:
        return "Spotify", "🟢"
    return "Universal Media", "⚡"


def human_bytes(size: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)"""
    if not size or size < 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    s = float(size)
    while s >= 1024.0 and i < len(units) - 1:
        s /= 1024.0
        i += 1
    return f"{s:.2f} {units[i]}"


def human_time(seconds: int) -> str:
    """Format duration in seconds to MM:SS or HH:MM:SS"""
    if not seconds or seconds < 0:
        return "0:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


URL_REGEX = re.compile(
    r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|[a-zA-Z0-9]+\.[^\s]{2,})'
)

def extract_url(text: str) -> Optional[str]:
    """Extract first valid HTTP/HTTPS URL from a string"""
    if not text:
        return None
    matches = URL_REGEX.findall(text)
    if matches:
        first = matches[0].strip()
        if not first.startswith("http"):
            first = "https://" + first
        return first
    return None
