import websockets
import json
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from os import getenv
from logging import getLogger
import tgbot


load_dotenv()
logger = getLogger()


url = "wss://ws-api.oneme.ru/websocket"
headers = {
    "Origin": "https://web.max.ru",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}
seq = 3


async def names_by_ids(ws: websockets.ClientConnection, ids: list[int]):
    global seq
    await ws.send(json.dumps({
        "ver": 11,
        "cmd": 0,
        "seq": seq,
        "opcode": 32,
        "payload": {
            "contactIds": ids
        }
    }))
    response = json.loads(await ws.recv())
    names = []
    for user in response["payload"]["contacts"]:
        fullname = user["names"][0]["firstName"] + user["names"][0]["lastName"]
        names.append(fullname)

    seq += 1

    return names


async def receiver_calback(ws: websockets.ClientConnection, msg: dict):
    if str(msg["payload"]["chatId"]) not in str(getenv("ALLOWED_MAX_CHATS")):
        return
    attaches = msg["payload"]["message"]["attaches"]
    text = msg["payload"]["message"]["text"]
    fullname = (await names_by_ids(ws, [msg["payload"]["message"]["sender"]]))[0]
    # if attaches:
    #     attaches_urls = [attach["baseUrl"] for attach in attaches]
    #     print(attaches_urls)

    if text:
        await tgbot.bot.send_message(
            getenv("TG_CHAT_ID"), 
            fullname+":\n  "+msg["payload"]["message"]["text"]
        )


async def message_receiver(ws: websockets.ClientConnection, callback):
    try:
        async for msg in ws:
            msgjson = json.loads(msg)
            if msgjson["opcode"] == 128:
                await callback(ws, msgjson)
                
    except websockets.ConnectionClosed:
        logger.info("Connection closed by server")


async def start_receiver(ws: websockets.ClientConnection, callback):
    asyncio.create_task(message_receiver(ws, callback))


async def send_auth(ws: websockets.ClientConnection):
    await ws.send(json.dumps(
        {
            "ver":11,
            "cmd":0,
            "seq":0,
            "opcode":6,
            "payload":{
                "userAgent":{
                    "deviceType":"WEB",
                    "locale":"ru",
                    "deviceLocale":"en",
                    "osVersion":"Windows",
                    "deviceName":"Chrome",
                    "headerUserAgent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "appVersion":"25.8.10","screen":"1080x1920 1.0x",
                    "timezone":"Europe/Saratov"
                },
                "deviceId":getenv("MAX_DEVICE_ID")
            }
        }
    ))

    await ws.send(json.dumps(
        {
            "ver":11,
            "cmd":0,
            "seq":2,
            "opcode":19,
            "payload": {
                "interactive":True,
                "token":getenv("MAX_PAYLOAD_TOKEN"),
                "chatsCount":40,
                "chatsSync":0,
                "contactsSync":0,
                "presenceSync":0,
                "draftsSync":0
            }
        }
    ))


async def connect():
    ws = await websockets.connect(url, additional_headers=headers)
    return ws


async def run():
    while True:
        ws = await connect()
        await send_auth(ws)
        await start_receiver(ws, receiver_calback)
        await ws.wait_closed()
