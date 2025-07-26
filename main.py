await asyncio.gather(
    telegram_bot(),
    app.run_task(host="0.0.0.0", port=8000)
)