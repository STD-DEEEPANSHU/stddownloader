# ⚡ StdDownloader Engine

High-performance, dual-engine media downloader microservice developed by **STD DEEPANSHU** under **TeamStdNetwork**.

Engineered for ultra-fast media extraction with **0.1-second instant cache delivery**, **YouTube Meow API**, **Telegram Assistant Userbot** proxying, and full **yt-dlp backup redundancy**.

---

## 🌟 Architecture & Features

| Tier | Component | Function |
|---|---|---|
| **Tier 0** | **0.1s Dump Channel Cache** | Checks `-1004458588038` and SQLite/Mongo. If media was downloaded before, delivers `file_id` instantly in 0.1s! |
| **Tier 1 (YouTube)** | **Meow / Yuki API** | Direct stream extraction (`/stream/{id}`) at maximum server throughput without IP bans. |
| **Tier 1 (Social)** | **Telegram Assistant Userbot** | Proxies extraction to helper bots pool (`@DPQbot` etc.), clicks resolution buttons, downloads and purges history. |
| **Tier 2 (Universal)** | **yt-dlp Backup Engine** | Universal fallback with mobile client spoofing (`android`, `ios`, `web_embedded`) if any primary engine fails. |
| **Tier 3** | **Dump Channel Archival** | Automatically sends fresh media to `-1004458588038` so the whole network reaps 0.1s cache benefits. |

---

## 🚀 Quick Start (Local Run)

```bash
# 1. Clone & Enter Directory
cd stddownloader

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment configuration
cp .env.sample .env

# 4. Start API Server
python main.py
```

Server runs at `http://localhost:8000`. Interactive Swagger UI available at `http://localhost:8000/docs`.

---

## 📡 API Endpoints

### 1. Download Media (GET)
```http
GET /api/download?url=https://www.instagram.com/reel/C8xY9zABCDE/&mode=video
```
**Response:**
```json
{
  "success": true,
  "cached": true,
  "platform": "Instagram",
  "platform_emoji": "🟣",
  "cache_key": "ig_C8xY9zABCDE_video",
  "file_id": "BAACAgUAAxkBAAI...",
  "dump_msg_id": 412,
  "title": "Instagram Media",
  "file_size": 14285000,
  "file_size_human": "13.62 MB",
  "delivery": "instant_dump_cache",
  "elapsed_seconds": 0.08
}
```

### 2. Download Media (POST)
```http
POST /api/download
Content-Type: application/json

{
  "url": "https://youtu.be/dQw4w9WgXcQ",
  "mode": "audio"
}
```

### 3. Check Cache
```http
GET /api/cache/check?url=https://youtu.be/dQw4w9WgXcQ&mode=video
```

---

## ☁️ Deploy to Heroku

1. Create a new Heroku app: `stddownloader`
2. Connect to GitHub repo and deploy `main` branch.
3. In Heroku Settings -> **Config Vars**:
   - `MEOW_API_KEY`: `yuki_feabaea9d68d372ee341424466c8d0ef`
   - `DUMP_CHANNEL`: `-1004458588038`
   - `HELPER_BOTS`: `DPQbot`
   - `STRING_SESSION`: *(optional, your userbot string session)*
   - `API_ID` & `API_HASH`: *(optional, for telegram)*
4. Dyno will boot automatically with `Procfile`!

---

## 👨‍💻 Author

- **Developer:** [STD DEEPANSHU](https://github.com/STD-DEEPANSHU)
- **Organization:** [TeamStdNetwork](https://github.com/TeamStdNetwork)
