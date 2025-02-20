import asyncio

from vkbottle import LoopWrapper, Bot

from config.config import api

w = LoopWrapper()
w.loop = asyncio.new_event_loop()
bot = Bot(api=api, loop_wrapper=w, )
