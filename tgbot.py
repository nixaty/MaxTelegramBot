from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaAudio, InputMediaDocument, InputMediaAnimation, BufferedInputFile
from dotenv import load_dotenv
from os import getenv
import asyncio


load_dotenv()


bot = Bot(getenv("TG_BOT_TOKEN"), default=DefaultBotProperties(
    parse_mode="MarkdownV2"
))
dp = Dispatcher()
