import websockets
import json
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from os import getenv


load_dotenv()


url = "wss://ws-api.oneme.ru/websocket"
headers = {
    "Origin": "https://web.max.ru",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}


async def message_receiver(ws: websockets.ClientConnection, callback):
    try:
        async for msg in ws:
            msgjson = json.loads(msg)
            if msgjson["opcode"] == 128:
                await callback(msgjson)
                
    except websockets.ConnectionClosed:
        print("Connection closed by server")


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
                    "osVersion":"Linux",
                    "deviceName":"Chrome",
                    "headerUserAgent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
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
            "seq":1,
            "opcode":5,
            "payload":{
                "events":[{
                    "type":"NAV",
                    "event":"COLD_START",
                    "userId":39406158,
                    "time":1756362822378,
                    "params":{
                        "session_id":1756362821575,
                        "action_id":1,
                        "screen_to":1
                    }
                }]
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


async def run(**kwargs):
    while True:
        ws = await connect()
        await send_auth(ws)
        await start_receiver(ws, kwargs["callback"])
        await ws.wait_closed()
