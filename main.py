import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from cc_downloader_bot import (
    API_ID, API_HASH, SESSION_STRING,
    command_listener, daily_summary, app
)

async def main():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    try:
        await client.connect()
        print("✅ Telegram client connected")

        # Start Telegram-related tasks
        await command_listener(client)
        asyncio.create_task(daily_summary())

        # Start Quart app on dynamic port
        PORT = int(os.getenv("PORT", "8000"))
        asyncio.create_task(app.run_task(host="0.0.0.0", port=PORT))

        # Keep bot running
        await client.run_until_disconnected()
    except Exception as e:
        print(f"🔥 Bot startup failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"❌ Main crash: {err}")
