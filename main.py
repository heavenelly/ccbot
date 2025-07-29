print(f"🌍 Running Quart on port: {get_port()}")
import os
import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from cc_downloader_bot import (
    API_ID, API_HASH, SESSION_STRING,
    command_listener, daily_summary, app
)

# ─── Port Fetcher ───
def get_port():
    return int(os.environ["PORT"])

async def main():
    print("🌐 Quart web server launching on dynamic port")

    # Telegram client setup
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()
    print("✅ Telegram client connected")
    print("🐣 Main.py version loaded successfully — July 28 midnight build")

    # Start command listener and daily summary task
    await command_listener(client)
    asyncio.create_task(daily_summary())

    # Run Telegram and Quart in the foreground together
    await asyncio.gather(
        client.run_until_disconnected(),
        app.run_task(host="0.0.0.0", port=get_port())
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"❌ Main crash: {err}")
