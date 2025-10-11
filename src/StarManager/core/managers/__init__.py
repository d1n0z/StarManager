from StarManager.core.managers.access_level import AccessLevelManager
from StarManager.core.managers.antispam_messages import AntispamMessagesManager
from StarManager.core.managers.chatusercmids import ChatUserCMIDsManager
from StarManager.core.managers.commands_cooldown import CommandsCooldownManager
from StarManager.core.managers.duel import DuelLockManager
from StarManager.core.managers.public_chats import PublicChatsManager
from StarManager.core.managers.raid import RaidManager
from StarManager.core.managers.rps import RPSManager
from StarManager.core.managers.xp import XPManager

antispam = AntispamMessagesManager()
commands_cooldown = CommandsCooldownManager()
duel_lock = DuelLockManager()
raid = RaidManager()
chat_user_cmids = ChatUserCMIDsManager()
access_level = AccessLevelManager()
rps = RPSManager()
public_chats = PublicChatsManager()
xp = XPManager()


to_init = [chat_user_cmids, access_level, rps, public_chats, xp]


async def initialize():
    for manager in to_init:
        await manager.initialize()


async def close():
    for manager in to_init:
        await manager.sync()
        await manager.close()
