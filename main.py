import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from cc_downloader_bot import (
    API_ID, API_HASH, SESSION_STRING,
    command_listener, daily_summary, app
)

async def main():
    # Initialize Telegram client with session
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    try:
        await client.connect()
        print("✅ Telegram client connected")

        # Start Telegram command listener
        await command_listener(client)

        # Create tasks for bot and daily summary
        asyncio.create_task(daily_summary())
        asyncio.create_task(app.run_task(host="0.0.0.0", port=8000))

        # Keep bot alive
        await client.run_until_disconnected()

    except Exception as e:
        print(f"💥 Bot startup failed: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"❌ Main crash: {err}")
