import websockets
import json
from datetime import datetime
import asyncio
import aiohttp
from dotenv import load_dotenv
from os import getenv
from logging import getLogger
import re
import tgbot


load_dotenv()
logger = getLogger(__name__)


ws_url = "wss://ws-api.oneme.ru/websocket"
ws_headers = {
    "Origin": "https://web.max.ru",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
}

message_format = "> {chat} \n{sender}:\n   {message}"
maximum_dload_file_size = 1024 * 1024 * 20

tg_chat_id = getenv("TG_CHAT_ID")


def escape_markdown_v2(text: str):
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)


async def check_file_size(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            size = resp.headers.get("Content-Length")
            if size == None:
                return None
            else:
                return int(size) <= maximum_dload_file_size


async def download_media(url: str):
    headers = {
        'User-Agent': ws_headers["User-Agent"],
        # 'Referer': 'https://vk.com/',
        'Accept': '*/*',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        # 'Origin': 'https://vk.com'
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            resp.raise_for_status()
            file = await resp.read()

            return file


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
        self.init_resp_payload = None

    async def _auth(self):
        auth_packets = await get_auth_requests()
        await self.send_request(6, auth_packets[0])
        self.init_resp_payload = (await self.send_request(19, auth_packets[1])).get("payload")

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
    
    chat_id = msg["payload"]["chatId"]
    uid = msg["payload"]["message"]["sender"]
    
    contacts = (await client.send_request(32, {"contactIds":[uid]}))["payload"]["contacts"]
    chats = client.init_resp_payload.get("chats")
    
    fullname = contacts[0]["names"][0]["firstName"] + " " + contacts[0]["names"][0]["lastName"]
    chat_title = None

    for chat in chats:
        if chat.get("id") == chat_id:
            chat_title = chat.get("title", "Direct Message")

    text = msg["payload"]["message"]["text"]
    attaches = msg["payload"]["message"]["attaches"]
    new_text = message_format.format(chat=chat_title, sender=fullname, message=escape_markdown_v2(text))
    
    if attaches:
        attaches_num = attaches.__len__()
        
        if attaches_num > 1:
            attach_inputs = []
            for attach in attaches:
                _attach_type = attach.get("_type")
                if _attach_type == "AUDIO":
                    attach_inputs.append(tgbot.InputMediaAudio(media=attach.get("url")))
                elif _attach_type == "PHOTO":
                    attach_inputs.append(tgbot.InputMediaPhoto(media=attach.get("baseUrl")))
                else:
                    attach_inputs.append(None)
                    await tgbot.bot.send_message(tg_chat_id, "Unsupported message")
                    return
            
            attach_inputs[0].caption = new_text
            await tgbot.bot.send_media_group(tg_chat_id, attach_inputs)
        elif attaches_num == 1:
            attach = attaches[0]
            attach_type = attach.get("_type")

            if attach_type == "AUDIO":
                url = attach.get("url")
                media = await download_media(url)
                await tgbot.bot.send_audio(tg_chat_id, tgbot.BufferedInputFile(media, "audio"), caption=new_text)

                # else:
                #     await tgbot.bot.send_message(tg_chat_id, f"{new_text}\n> Files were not sent because they exceed the maximum allowed size")

            elif attach_type == "PHOTO":
                url = attach.get("baseUrl")
                await tgbot.bot.send_photo(tg_chat_id, url, caption=new_text)
            else:
                await tgbot.bot.send_message(tg_chat_id, f"{new_text}\n> Unsupported message")

    elif text:
        await tgbot.bot.send_message(
            tg_chat_id, 
            new_text,
        )


async def on_update(client: MaxWSClient, msg: dict):
    payload = msg["payload"]

    if msg["opcode"] == 128:
        if msg["payload"]["message"].get("status") == None:
            await forward_message(client, msg)


async def start():
    max = MaxWSClient(ws_url, ws_headers)
    await max.start()

    # Register events
    max.on_event(on_update)

    logger.info("MAX bot started")
