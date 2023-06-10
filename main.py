import asyncio
import logging
import json

from aiogram.utils import executor
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from BotAssistant import VirtualBotAssistant

def read_config():
    with open('config.json') as config_file:
        return json.load(config_file)


logging.basicConfig(level=logging.INFO)

bot = Bot(read_config()["TOKEN"])
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


if __name__ == '__main__':
    assistant = VirtualBotAssistant(bot, dp)
    loop = asyncio.get_event_loop()
    executor.start_polling(dp)
