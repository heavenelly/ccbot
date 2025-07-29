import os, asyncio, random
from datetime import datetime
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel
from quart import Quart
from asyncio import Queue

# ─── Load Environment Variables ───
load_dotenv()
API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID", "0"))
PORT = int(os.getenv("PORT", "8000"))

# ─── Constants ───
CHANNEL_LINK = -1001181373341
VALID_EXTENSIONS = (".package", ".zip", ".rar")
APPROVED_CREATORS = [
    "okruee", "serenity", "joliebean", "myshunosun", "syboulette", "leosims",
    "ellcrze", "oni", "caio", "sinsimcc", "jellypaws", "simstrouble", "plushpixels",
    "peachyfaerie", "lamatisse", "pixelvibes", "pimpmysims4", "simspirationbuilds",
    "thecluttercat", "foreverdesigns", "nostylexwoodland", "bostyny", "heybrine", "arethabee"
]
CATEGORY_MAP = {
    "build": ["build", "walls", "floors", "windows", "doors"],
    "buy": ["buy", "objects", "clutter", "furniture", "decor"],
    "cc": ["cas", "hair", "outfit", "skin", "eyes", "clothing", "makeup"],
    "gameplay_mods": ["mod", "script", "gameplay", "mechanic"]
}
MOODS = [
    "✨ feeling clutter-compatible",
    "🌸 manifesting build mode beauty",
    "📦 organizing aesthetic downloads",
    "🧃 hydrated and ready to fetch CC",
    "🎀 vibing with creators today"
]

# ─── Globals ───
download_log = []
notification_queue = Queue()
app = Quart(__name__)

# ─── Quart Routes ───
@app.route("/")
async def ping(): return "OK 👋"

@app.route("/kaithhealthcheck")
async def health(): return {"status": "ok"}

@app.route("/kaithversion")
async def version():
    return {
        "version": "v1.0.3",
        "status": "Kaith is awake and sparkling ✨",
        "mood": random.choice(MOODS)
    }

# ─── Notification System ───
async def send_notification(text: str):
    await notification_queue.put(text)

async def notification_worker(user_client):
    while True:
        text = await notification_queue.get()
        try:
            await user_client.send_message(NOTIFY_USER_ID, f"@youngbusiness_woman {text}")
            await asyncio.sleep(1.5)
        except Exception as e:
            print(f"❌ Notification error: {text} — {e}")

# ─── File Handling ───
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
            await send_notification(f"⛔️ Skipped — no approved creator in: {filename}")
            return
        if not filename or not filename.lower().endswith(VALID_EXTENSIONS):
            await send_notification(f"📭 Skipped unsupported file: {filename}")
            return
        category = detect_category(text, filename)
        folder = os.path.join("downloads", category)
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, filename)
        if os.path.exists(path):
            await send_notification(f"🔁 Skipped duplicate: {filename}")
            return
        await msg.download_media(file=path)
        await send_notification(f"✅ {source} saved: /{category}/{filename}")
        download_log.append(filename)
    except Exception as e:
        await send_notification(f"⚠️ {source} failed: {filename} — {e}")

# ─── Backfill History ───
async def scan_channel_history(user_client, limit=5000):
    try:
        channel = await user_client.get_entity(PeerChannel(CHANNEL_LINK))
        async for msg in user_client.iter_messages(channel, reverse=True, limit=limit):
            await download_if_valid(msg, "channel-history")
            await asyncio.sleep(0.5)
        await send_notification("🗂 Finished scanning channel")
    except Exception as e:
        await send_notification(f"❌ History scan failed: {e}")

# ─── Command Handlers ───
async def command_listener(bot_client):
    @bot_client.on(events.NewMessage(pattern="/summary"))
    async def summary_handler(event):
        try:
            if download_log:
                summary = "\n".join(f"— {f} ✅" for f in download_log)
                message = f"📊 Today's Downloads:\n{summary}"
            else:
                message = "📊 No CC downloaded yet today."
            await bot_client.send_message(event.chat_id, message)
        except Exception as e:
            print(f"⚠️ Summary error: {e}")

    @bot_client.on(events.NewMessage(pattern="/ping"))
    async def ping_handler(event):
        try:
            mood = random.choice(MOODS)
            message = f"🟢 Kaith is online!\n{mood.capitalize()}."
            await bot_client.send_message(event.chat_id, message)
        except Exception as e:
            print(f"⚠️ Ping error: {e}")

# ─── Daily Summary ───
async def daily_summary():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            try:
                summary = "\n".join(f"— {f} ✅" for f in download_log) if download_log else "📊 No CC downloaded today."
                await send_notification(f"📊 Daily Summary:\n{summary}")
                download_log.clear()
            except Exception as e:
                print(f"⚠️ Summary dispatch failed: {e}")
        await asyncio.sleep(60)

# ─── Entrypoint ───
async def run_kaith_dual():
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await user_client.connect()

    bot_client = await TelegramClient("bot.session", API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)
    print("🚀 Kaith dual-client ready")

    # Background tasks
    asyncio.create_task(notification_worker(user_client))
    asyncio.create_task(daily_summary())

    # Bot functionality
    await scan_channel_history(user_client)
    @user_client.on(events.NewMessage(chats=CHANNEL_LINK))
    async def channel_listener(event):
        await download_if_valid(event.message, "channel")
    await command_listener(bot_client)

    # Start Quart web server (primary event loop task)
    await app.run_task(host="0.0.0.0", port=PORT)

if __name__ == "__main__":
    asyncio.run(run_kaith_dual())
