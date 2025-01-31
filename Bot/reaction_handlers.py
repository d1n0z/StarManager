from vkbottle import GroupTypes

from Bot.utils import getUserAccessLevel, getUserPremium, getUserPremmenuSetting, getChatCommandLevel, deleteMessages, \
    getUserLeague
from config.config import COMMANDS, API


async def reaction_handle(event: GroupTypes.MessageReactionEvent) -> None:
    if event.object.reaction_id != 2:
        return
    uid = event.object.reacted_id

    if (not (await getUserPremium(uid) or await getUserLeague(uid)) or
            not await getUserPremmenuSetting(uid, 'clear_by_fire', 1)):
        return

    chat_id = event.object.peer_id - 2000000000
    if (u_acc := await getUserAccessLevel(uid, chat_id)) < await getChatCommandLevel(
            chat_id, 'clear', COMMANDS['clear']):
        return

    cmid = event.object.cmid
    if await getUserAccessLevel((await API.messages.get_by_conversation_message_id(
            peer_id=event.object.peer_id, conversation_message_ids=cmid)).items[0].from_id, chat_id) <= u_acc:
        await deleteMessages(cmid, chat_id)
