import os, asyncio, random
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import UsernameNotOccupiedError
from quart import Quart
from config import (
    SESSION_STRING, API_ID, API_HASH, TELEGRAM_TOKEN,
    NOTIFY_USER_ID, CHANNEL_LINK
)

app = Quart(__name__)
download_log = []
MOODS = ["purring", "sleepy", "curious", "ready to fetch files"]

# ─── Notification Fix ───
async def send_notification(text):
    if NOTIFY_USER_ID and NOTIFY_USER_ID > 0:
        try:
            user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
            await user_client.connect()
            entity = await user_client.get_input_entity(NOTIFY_USER_ID)
            await user_client.send_message(entity, f"@youngbusiness_woman {text}")
            await user_client.disconnect()
        except Exception as e:
            print(f"⚠️ Notification failed for {NOTIFY_USER_ID}: {e}")
    else:
        print("⚠️ Skipping notification — invalid NOTIFY_USER_ID")

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

    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await user_client.connect()
    bot_client = await TelegramClient("bot.session", API_ID, API_HASH).start(bot_token=TELEGRAM_TOKEN)
    print("🚀 Kaith dual-client ready")

    asyncio.create_task(daily_summary())
    asyncio.create_task(command_listener(bot_client))

    @user_client.on(events.NewMessage(chats=CHANNEL_LINK))
    async def channel_listener(event):
        # Replace with your download logic
        download_log.append(f"Downloaded file: {event.message.message}")

    await app.run_task(host="0.0.0.0", port=int(os.environ["PORT"]))

if __name__ == "__main__":
    try:
        asyncio.run(run_kaith_dual())
    except Exception as e:
        print(f"❌ Main crash: {e}")
