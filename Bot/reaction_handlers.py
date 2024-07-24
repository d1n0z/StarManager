from vkbottle.bot import MessageReactionEvent

from Bot.utils import getUserAccessLevel, getUserPremium, getUserPremmenuSetting, getChatCommandLevel, deleteMessages
from config.config import COMMANDS, API


async def reaction_handle(event: MessageReactionEvent) -> None:
    reaction_id = event.reaction_id
    if reaction_id is None:
        return
    uid = event.user_id
    cmid = event.conversation_message_id
    chat_id = event.peer_id - 2000000000
    u_acc = await getUserAccessLevel(uid, chat_id)
    u_premium = await getUserPremium(uid)
    clear_by_fire = await getUserPremmenuSetting(uid, 'clear_by_fire', 1)

    if u_premium == 0:
        return
    if reaction_id != 2 or not clear_by_fire:
        return

    command_acc = await getChatCommandLevel(chat_id, 'clear', COMMANDS['clear'])

    if u_acc < command_acc:
        return

    id = await API.messages.get_by_conversation_message_id(event.peer_id, cmid)
    id = id.items[0].from_id
    chacc = await getUserAccessLevel(id, chat_id)
    if chacc <= u_acc:
        await deleteMessages(cmid, chat_id)
