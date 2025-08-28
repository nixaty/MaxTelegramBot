from tgbot import dp
from aiogram import filters, types


@dp.message(filters.Command("start"))
async def on_command_start(msg: types.Message):
    await msg.answer("start")
