from vkbottle import GroupTypes

from StarManager.core.utils import (
    get_user_access_level,
    get_user_premium,
    get_user_premmenu_setting,
    get_chat_command_level,
    delete_messages,
    get_user_league,
)
from StarManager.core.config import settings, api


async def reaction_handle(event: GroupTypes.MessageReactionEvent) -> None:
    if event.object.reaction_id != 2:
        return
    uid = event.object.reacted_id

    if not (
        await get_user_premium(uid) or await get_user_league(uid) >= 2
    ) or not await get_user_premmenu_setting(uid, "clear_by_fire", 1):
        return

    chat_id = event.object.peer_id - 2000000000
    if (
        u_acc := await get_user_access_level(uid, chat_id)
    ) < await get_chat_command_level(
        chat_id, "clear", settings.commands.commands["clear"]
    ):
        return

    cmid = event.object.cmid
    try:
        if (
            await get_user_access_level(
                (
                    await api.messages.get_by_conversation_message_id(
                        peer_id=event.object.peer_id, conversation_message_ids=[cmid]
                    )
                )
                .items[0]
                .from_id,
                chat_id,
            )
            <= u_acc
        ):
            await delete_messages(cmid, chat_id)
    except Exception:
        pass
