import asyncio
from cc_downloader_bot import (
    TelegramClient, 
    StringSession, 
    SESSION_STRING, 
    API_ID, 
    API_HASH, 
    command_listener,
    download_if_valid,
    CHANNEL_LINK,
    app,  # Quart ping server
    daily_summary
)
from telethon import events

async def telegram_bot():
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.connect()  # ✅ uses existing session, no input prompt
    await command_listener(client)

    # 📨 Channel monitoring
    @client.on(events.NewMessage(chats=CHANNEL_LINK))
    async def handler(event):
        if event.document:
            await download_if_valid(event.message, "Telegram")

    print("🎮 Telegram bot is live.")
    await client.run_until_disconnected()

async def main():
    await asyncio.gather(
        telegram_bot(),
        app.run_task(host="0.0.0.0", port=8000),  # 🚀 Quart ping server
        daily_summary()  # 📊 Daily report scheduler
    )

if __name__ == "__main__":
    asyncio.run(main())
