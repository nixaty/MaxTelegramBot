import websockets
import json
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from os import getenv
from logging import getLogger
import tgbot


load_dotenv()
logger = getLogger(__name__)


url = "wss://ws-api.oneme.ru/websocket"
headers = {
    "Origin": "https://web.max.ru",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}


async def get_auth_requests():
    return [
        {
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
        },
        {
            "interactive":True,
            "token":getenv("MAX_PAYLOAD_TOKEN"),
            "chatsCount":40,
            "chatsSync":0,
            "contactsSync":0,
            "presenceSync":0,
            "draftsSync":0
        }

    ]


class MaxWSClient:
    def __init__(self, url, additional_headers):
        self.url = url
        self.additional_headers = additional_headers
        self.last_seq = -1
        self.pending = {}
        self.event_handlers = []

    async def _auth(self):
        auth_packets = await get_auth_requests()
        await self.send_request(6, auth_packets[0])
        await self.send_request(19, auth_packets[1])

    async def _connect(self):
        while True:
            self.last_seq = -1
            self.pending = {}

            self.ws = await websockets.connect(self.url, additional_headers=self.additional_headers)
            asyncio.create_task(self._reader())
            await self._auth()
            await self.ws.wait_closed()

    async def start(self):
        asyncio.create_task(self._connect())
        await asyncio.sleep(1)

    async def _reader(self):
        try:
            async for msg in self.ws:
                data = json.loads(msg)

                seq = data["seq"]
                opcode = data["opcode"]

                if seq is not None and seq > self.last_seq:
                    self.last_seq = seq

                if seq in self.pending:
                    record = self.pending[seq]
                    fut, expected_opcode = record["future"], record["opcode"]

                    if opcode == expected_opcode:
                        if not fut.done():
                            fut.set_result(data)
                        self.pending.pop(seq)
                        continue

                for handler in self.event_handlers:
                    asyncio.create_task(handler(self, data))

        except websockets.ConnectionClosed:
            logger.info("Connection closed by server. Reconnecting")


    async def send_request(self, opcode, payload):
        self.last_seq += 1
        seq = self.last_seq

        packet = {
            "ver": 11,
            "cmd": 0,
            "seq": seq,
            "opcode": opcode,
            "payload": payload,
        }

        fut = asyncio.get_event_loop().create_future()
        self.pending[seq] = {"future": fut, "opcode": opcode}

        await self.ws.send(json.dumps(packet))
        return await fut


    def on_event(self, callback):
        self.event_handlers.append(callback)


async def forward_message(client: MaxWSClient, msg: dict):
    if str(msg["payload"]["chatId"]) not in str(getenv("ALLOWED_MAX_CHATS")):
        return

    uid = msg["payload"]["message"]["sender"]
    contacts = (await client.send_request(32, {"contactIds":[uid]}))["payload"]["contacts"]
    fullname = contacts[0]["names"][0]["firstName"] + " " + contacts[0]["names"][0]["lastName"]

    text = msg["payload"]["message"]["text"]
    attaches = msg["payload"]["message"]["attaches"]
    
    # if attaches:
    #     attaches_urls = [attach["baseUrl"] for attach in attaches]
    #     print(attaches_urls)

    if text:
        await tgbot.bot.send_message(
            getenv("TG_CHAT_ID"), 
            fullname+":\n  "+msg["payload"]["message"]["text"]
        )


async def on_update(client: MaxWSClient, msg: dict):
    payload = msg["payload"]

    if msg["opcode"] == 128:
        await forward_message(client, msg)


async def start():
    max = MaxWSClient(url, headers)

    await max.start()

    # Register events
    max.on_event(on_update)

    logger.info("MAX bot started")
