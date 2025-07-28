import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
from quart import Quart

# ─── Load secrets safely ───
load_dotenv()
try:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    NOTIFY_BOT_TOKEN = os.getenv("NOTIFY_BOT_TOKEN", "")
    NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID", "0"))
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    if not all([API_ID, API_HASH, SESSION_STRING]):
        raise ValueError("❌ Missing required env vars: API_ID, API_HASH, or SESSION_STRING")
except Exception as e:
    print(f"🚨 Env setup failed: {e}")
    raise SystemExit(1)

CHANNEL_LINK = -1001181373341

APPROVED_CREATORS = [
    "okruee", "simstrouble", "ellcrze", "oni", "sinsimcc", "jellypaws", "caio",
    "serenity", "joliebean", "plushpixels", "peachyfaerie", "lamatisse",
    "myshunosun", "syboulette", "pixelvibes", "pimpmysims4",
    "simspirationbuilds", "thecluttercat", "foreverdesigns",
    "nostylexwoodland", "bostyny", "heybrine", "arethabee", "leosims"
]

VALID_EXTENSIONS = (".package", ".zip", ".rar")

CATEGORY_MAP = {
    "build": ["build", "walls", "floors", "windows", "doors"],
    "buy": ["buy", "objects", "clutter", "furniture", "decor"],
    "cc": ["cas", "hair", "outfit", "skin", "eyes", "clothing", "makeup"],
    "gameplay_mods": ["mod", "script", "gameplay", "mechanic"]
}

download_log = []

# ─── Quart Ping Server ───
app = Quart(__name__)

@app.route("/")
async def ping():
    return "OK 👋"

# ─── Telegram Notification ───
async def send_notification(text: str):
    try:
        async with TelegramClient("notify_bot", API_ID, API_HASH) as bot:
            await bot.start(bot_token=NOTIFY_BOT_TOKEN)
            await bot.send_message(NOTIFY_USER_ID, f"@youngbusiness_woman {text}")
            print(f"✅ Notification sent: {text}")
    except Exception as e:
        print(f"❌ Notification error: {e}")

# ─── Daily Summary ───
async def daily_summary():
    print("✅ Daily summary coroutine running...")
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                if download_log:
                    summary = "\n".join(f"— {f} ✅" for f in download_log)
                    message = f"📊 Daily Download Summary:\n{summary}\nTotal: {len(download_log)} files"
                else:
                    message = "📊 No CC downloaded today."
                await send_notification(message)
                download_log.clear()
            except Exception as e:
                print(f"⚠️ Summary dispatch failed: {e}")
        await asyncio.sleep(60)

# ─── Command Handler ───
async def command_listener(client):
    @client.on(events.NewMessage(pattern="/summary"))
    async def summary_handler(event):
        try:
            if download_log:
                summary = "\n".join(f"— {f} ✅" for f in download_log)
                message = f"📊 Today's Downloads:\n{summary}\nTotal: {len(download_log)} files"
            else:
                message = "📊 No CC downloaded yet today."
            await client.send_message(event.chat_id, f"@youngbusiness_woman {message}")
        except Exception as e:
            print(f"⚠️ Command response error: {e}")

# ─── Category Detection ───
def detect_category(text, filename):
    combined = f"{text} {filename}".lower()
    for folder, keywords in CATEGORY_MAP.items():
        if any(k in combined for k in keywords):
            return folder
    return "uncategorized"

# ─── File Validation & Download ───
async def download_if_valid(msg, source: str):
    try:
        text = f"{msg.message or ''} {msg.text or ''} {msg.raw_text or ''}".lower()
        filename = msg.file.name if msg.document else ""
        combined = f"{text} {filename}".lower()

        print(f"📝 Message text: {text}")
        print(f"🗂 Filename: {filename}")

        if not any(c in combined for c in APPROVED_CREATORS):
            await send_notification(f"⛔️ Skipped — no approved creator found in: {filename}")
            return

        if not filename or not filename.lower().endswith(VALID_EXTENSIONS):
            await send_notification(f"📭 Skipped unsupported file type: {filename}")
            return

        category = detect_category(text, filename)
        folder = os.path.join("downloads", category)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)

        if os.path.exists(path):
            await send_notification(f"🔁 Skipped duplicate: {filename}")
            return

        print(f"📥 Downloading ({source}) to /{category}: {filename}")
        await msg.download_media(file=path)
        await send_notification(f"✅ {source} CC saved in /{category}: {filename}")
        download_log.append(filename)

    except Exception as e:
        await send_notification(f"⚠️ {source} download failed: {filename} — {e}")
        print(f"💥 Exception in download_if_valid: {e}")

# ─── Exported Symbols ───
__all__ = [
    "TelegramClient",
    "StringSession",
    "SESSION_STRING",
    "API_ID",
    "API_HASH",
    "CHANNEL_LINK",
    "command_listener",
    "download_if_valid",
    "app",
    "daily_summary"
]
