import os
import re
import asyncio
import random
from datetime import datetime
from fastapi import FastAPI
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ─── Constants & Globals ───
API_ID = os.environ["API_ID"]
API_HASH = os.environ["API_HASH"]
SESSION_STRING = os.environ["SESSION_STRING"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHANNEL_LINK = os.environ["CHANNEL_LINK"]

download_log = []
MOODS = ["purring", "sleepy", "curious", "ready to fetch files"]
app = FastAPI()

# ─── Self-Notify ───
async def send_notification(text):
    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await user_client.connect()
    try:
        await user_client.send_message("me", f"📥 Kaith Update:\n{text}")
        print("✅ Notification sent")
    except Exception as e:
        print(f"⚠️ Notification failed: {e}")
    finally:
        await user_client.disconnect()

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
    print(f"🌍 Final port bind: {int(os.environ['PORT'])}")

    user_client = await TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH).start()
    bot_client = await TelegramClient("bot.session", API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)
    print("🚀 Kaith dual-client ready")

    asyncio.create_task(daily_summary())
    asyncio.create_task(command_listener(bot_client))

    @user_client.on(events.NewMessage(chats=CHANNEL_LINK))
    async def channel_listener(event):
        file_name = event.message.message
        if re.search(r'\.(zip|rar|pdf|docx|txt)$', file_name, re.IGNORECASE):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            formatted = f"[{timestamp}] {file_name}"
            download_log.append(formatted)
            print(f"📥 Logged from channel: {formatted}")
            await send_notification(f"📥 New CC drop:\n{file_name}")
        else:
            print(f"⚠️ Ignored non-CC message: {file_name}")

    @app.get("/health")
    async def health():
        return {"status": "Kaith is alive 💚"}

# ─── Main Runner ───
if __name__ == "__main__":
    try:
        asyncio.run(run_kaith_dual())
    except Exception as e:
        print(f"❌ Main crash: {e}")
