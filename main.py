import asyncio
import websockets
import json
from datetime import datetime
import logging
import dotenv
from os import getenv
import tgbot
import tgbot_handlers
import maxapi


async def main():
    ws = await maxapi.connect()
    print(ws.id)
    await maxapi.run()
    await tgbot.bot.delete_webhook(drop_pending_updates=True)
    await tgbot.dp.start_polling(tgbot.bot, allowed_updates=tgbot.dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
