from aiogram import types, BaseMiddleware
from aiogram.fsm.context import FSMContext


class ContextMsgDeleteMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event,
        data,
    ):
        state: FSMContext | None = data.get("state")
        if state:
            state_data = await state.get_data()
            if "msg" in state_data:
                msg: types.Message = state_data["msg"]
                try:
                    await msg.delete()
                except Exception:
                    pass
        await handler(event, data)
