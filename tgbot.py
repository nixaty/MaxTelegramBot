from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from os import getenv
import asyncio


load_dotenv()


bot = Bot(getenv("TG_BOT_TOKEN"))
dp = Dispatcher()
