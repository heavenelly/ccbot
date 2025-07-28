import os
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from dotenv import load_dotenv
from quart import Quart
from asyncio import Queue

# ─── Load Environment Variables ───
load_dotenv()
try:
    API_ID = int(os.getenv("API_ID", "0"))
    API_HASH = os.getenv("API_HASH", "")
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID", "0"))
    if not all([API_ID, API_HASH, SESSION_STRING, TELEGRAM_TOKEN]):
        raise ValueError("❌ Missing required env vars")
except Exception as e:
    print(f"🚨 Env setup failed: {e}")
    raise SystemExit(1)

# ─── Constants ───
CHANNEL_LINK = -1001181373341
VALID_EXTENSIONS = (".package", ".zip", ".rar")
APPROVED_CREATORS = [ "okruee", "simstrouble", "ellcrze", "oni", "sinsimcc", "jellypaws", "caio", "serenity", "joliebean", "plushpixels", "peachyfaerie", "lamatisse", "myshunosun", "syboulette", "pixelvibes", "pimpmysims4", "simspirationbuilds", "thecluttercat", "foreverdesigns", "nostylexwoodland", "bostyny", "heybrine", "arethabee", "leosims" ]
CATEGORY_MAP = {
    "build": ["build", "walls", "floors", "windows", "doors"],
    "buy": ["buy", "objects", "clutter", "furniture", "decor"],
    "cc": ["cas", "hair", "outfit", "skin", "eyes", "clothing", "makeup"],
    "gameplay_mods": ["mod", "script", "gameplay", "mechanic"]
}
download_log = []
notification_queue = Queue()

# ─── Quart API ───
app = Quart(__name__)

@app.route("/")
async def ping():
    return "OK 👋"

@app.route("/kaithhealthcheck")
async def kaith_healthcheck():
    return {"status": "ok"}

@app.route("/kaithheathcheck")
async def typo_healthcheck():
    return {"status": "ok"}

# ─── Notification System ───
async def send_notification(text: str):
    await notification_queue.put(text)

async def notification_worker(user_client):
    while True:
        text = await notification_queue.get()
        try:
            await user_client.send_message(NOTIFY_USER_ID, f"@youngbusiness_woman {text}")
            print(f"✅ Notification sent: {text}")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"❌ Notification error: {text} — {e}")

# ─── File Processing ───
def detect_category(text, filename):
    combined = f"{text} {filename}".lower()
    for folder, keywords in CATEGORY_MAP.items():
        if any(k in combined for k in keywords):
            return folder
    return "uncategorized"

async def download_if_valid(msg, source: str):
    try:
        text = f"{msg.message or ''} {msg.text or ''} {msg.raw_text or ''}".lower()
        filename = msg.file.name if msg.document else ""
        if not any(c in f"{text} {filename}" for c in APPROVED_CREATORS):
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
        await msg.download_media(file=path)
        await send_notification(f"✅ {source} CC saved in /{category}: {filename}")
        download_log.append(filename)
    except Exception as e:
        await send_notification(f"⚠️ {source} download failed: {filename} — {e}")

# ─── Summary & Commands ───
async def daily_summary():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                summary = "\n".join(f"— {f} ✅" for f in download_log) if download_log else "📊 No CC downloaded today."
                await send_notification(f"📊 Daily Download Summary:\n{summary}")
                download_log.clear()
            except Exception as e:
                print(f"⚠️ Summary dispatch failed: {e}")
        await asyncio.sleep(60)

async def command_listener(bot_client):
    @bot_client.on(events.NewMessage(pattern="/summary"))
    async def summary_handler(event):
        try:
            if download_log:
                summary = "\n".join(f"— {f} ✅" for f in download_log)
                message = f"📊 Today's Downloads:\n{summary}\nTotal: {len(download_log)} files"
            else:
                message = "📊 No CC downloaded yet today."
            await bot_client.send_message(event.chat_id, f"@youngbusiness_woman {message}")
        except Exception as e:
            print(f"⚠️ Command response error: {e}")

# ─── Entrypoint ───
async def run_kaith_dual():
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    bot_client = TelegramClient("bot.session", API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)

    await user_client.connect()
    await bot_client.connect()
    print("🚀 Kaith dual-client ready")

    @user_client.on(events.NewMessage(chats=CHANNEL_LINK))
    async def channel_listener(event):
        await download_if_valid(event.message, "channel")

    await command_listener(bot_client)
    asyncio.create_task(notification_worker(user_client))
    asyncio.create_task(daily_summary())
    asyncio.create_task(app.run_task(host="0.0.0.0", port=8080))

    await asyncio.gather(user_client.run_until_disconnected(), bot_client.run_until_disconnected())

if __name__ == "__main__":
    asyncio.run(run_kaith_dual())
