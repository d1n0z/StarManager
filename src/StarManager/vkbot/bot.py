import asyncio

from vkbottle import LoopWrapper, Bot

from StarManager.core.config import api

w = LoopWrapper()
w.loop = asyncio.new_event_loop()
bot = Bot(api=api, loop_wrapper=w, )
