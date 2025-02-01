from typing import Dict, Callable, Any, Awaitable

from aiogram import types, BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject


class ContextMsgDeleteMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event, data):
        state: FSMContext = data.get('state')
        if state:
            state_data = await state.get_data()
            if 'msg' in state_data:
                msg: types.Message = state_data['msg']
                try:
                    await msg.delete()
                except:
                    pass
        await handler(event, data)
