import time

from vkbottle.bot import Message
from vkbottle.framework.labeler import BotLabeler

from StarManager.core import managers
from StarManager.core.config import settings
from StarManager.core.utils import (
    get_chat_access_name,
    get_user_access_level,
    get_user_mute,
    get_user_name,
    get_user_nickname,
    messagereply,
    search_id_in_message,
    set_chat_mute,
    set_user_access_level,
)
from StarManager.vkbot import keyboard, messages
from StarManager.vkbot.rules import SearchCMD

bl = BotLabeler()


@bl.chat_message(SearchCMD("unmute"))
async def unmute(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unmute_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )

    if await get_user_access_level(id, chat_id) >= await get_user_access_level(
        uid, chat_id
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.unmute_higher()
        )

    if await get_user_mute(id, chat_id) <= time.time():
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.unmute_no_mute(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )

    await managers.mute.unmute(id, chat_id)
    await set_chat_mute(id, chat_id, 0)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.unmute(
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            uid,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            id,
        ),
        keyboard=keyboard.deletemessages(uid, [message.conversation_message_id]),
    )


@bl.chat_message(SearchCMD("mutelist"))
async def mutelist(message: Message):
    now = time.time()
    res = [
        i
        for i in await managers.mute.get_all(message.peer_id - 2000000000)
        if i.mute > now
    ]
    muted_count = len(res)
    res = sorted(
        res[:30],
        key=lambda i: i.uid,
        reverse=True,
    )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.mutelist(res, muted_count),
        keyboard=keyboard.mutelist(message.from_id, 0, muted_count),
    )


@bl.chat_message(SearchCMD("unwarn"))
async def unwarn(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unwarn_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if id == uid:
        return await messagereply(
            message, disable_mentions=1, message=await messages.unwarn_myself()
        )

    if await get_user_access_level(id, chat_id) >= await get_user_access_level(
        uid, chat_id
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.unwarn_higher()
        )

    if not await managers.warn.unwarn(id, chat_id):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.unwarn_no_warns(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.unwarn(
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            uid,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            id,
        ),
        keyboard=keyboard.deletemessages(uid, [message.conversation_message_id]),
    )


@bl.chat_message(SearchCMD("warnlist"))
async def warnlist(message: Message):
    res = [
        i
        for i in await managers.warn.get_all(message.peer_id - 2000000000)
        if i and i.warns > 0
    ]
    count = len(res)
    res = sorted(res[:30], key=lambda i: i.uid, reverse=True)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.warnlist(res, count),
        keyboard=keyboard.warnlist(message.from_id, 0, count),
    )


@bl.chat_message(SearchCMD("setaccess"))
async def setaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    data = message.text.split()
    id = await search_id_in_message(message.text, message.reply_message)
    if (
        not id
        or (len(data) + bool(message.reply_message) < 3)
        or not data[-1].isdigit()
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.setacc_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if id == uid and uid not in settings.service.main_devs:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setaccess_myself()
        )

    acc = int(data[-1])
    if not (0 < acc < 7) and uid not in settings.service.main_devs:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setacc_hint()
        )

    ch_acc = await managers.access_level.get(id, chat_id)
    if ch_acc and ch_acc.custom_level_name is not None:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.setaccess_has_custom_level(),
        )
    if acc == (ch_acc.access_level if ch_acc else 0):
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.setacc_already_have_acc(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )

    u_acc = await get_user_access_level(uid, chat_id)
    if not (acc < u_acc or u_acc >= 8) and uid not in settings.service.main_devs:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setacc_low_acc(acc)
        )
    if (
        ch_acc.access_level if ch_acc else 0
    ) >= u_acc and uid not in settings.service.main_devs:
        return await messagereply(
            message, disable_mentions=1, message=await messages.setacc_higher()
        )

    await set_user_access_level(id, chat_id, acc)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.setacc(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            acc,
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
            await get_chat_access_name(chat_id, acc),
        ),
    )


@bl.chat_message(SearchCMD("delaccess"))
async def delaccess(message: Message):
    chat_id = message.peer_id - 2000000000
    uid = message.from_id
    id = await search_id_in_message(message.text, message.reply_message)
    if not id:
        return await messagereply(
            message, disable_mentions=1, message=await messages.delaccess_hint()
        )
    if id < 0:
        return await messagereply(
            message, disable_mentions=1, message=await messages.id_group()
        )
    if id == uid and uid not in settings.service.devs:
        return await messagereply(
            message, disable_mentions=1, message=await messages.delaccess_myself()
        )

    ch_acc = await managers.access_level.get(id, chat_id)
    if ch_acc and ch_acc.custom_level_name is not None:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.setaccess_has_custom_level(),
        )
    if not ch_acc or not ch_acc.access_level:
        return await messagereply(
            message,
            disable_mentions=1,
            message=await messages.delaccess_noacc(
                id, await get_user_name(id), await get_user_nickname(id, chat_id)
            ),
        )
    if (
        ch_acc.access_level >= await get_user_access_level(uid, chat_id)
        and uid not in settings.service.devs
    ):
        return await messagereply(
            message, disable_mentions=1, message=await messages.delaccess_higher()
        )
    await set_user_access_level(id, chat_id, 0)
    await messagereply(
        message,
        disable_mentions=1,
        message=await messages.delaccess(
            uid,
            await get_user_name(uid),
            await get_user_nickname(uid, chat_id),
            id,
            await get_user_name(id),
            await get_user_nickname(id, chat_id),
        ),
    )
