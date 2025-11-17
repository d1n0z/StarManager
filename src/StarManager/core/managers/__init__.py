from StarManager.core.managers.access_level import AccessLevelManager
from StarManager.core.managers.antispam_messages import AntispamMessagesManager
from StarManager.core.managers.chat_settings import ChatSettingsManager
from StarManager.core.managers.chatusercmids import ChatUserCMIDsManager
from StarManager.core.managers.commands_cooldown import CommandsCooldownManager
from StarManager.core.managers.duel import DuelLockManager
from StarManager.core.managers.public_chats import PublicChatsManager
from StarManager.core.managers.raid import RaidManager
from StarManager.core.managers.rps import RPSManager
from StarManager.core.managers.xp import XPManager

managers = [
    access_level := AccessLevelManager(),
    antispam := AntispamMessagesManager(),
    chat_settings := ChatSettingsManager(),
    chat_user_cmids := ChatUserCMIDsManager(),
    commands_cooldown := CommandsCooldownManager(),
    duel_lock := DuelLockManager(),
    public_chats := PublicChatsManager(),
    raid := RaidManager(),
    rps := RPSManager(),
    xp := XPManager(),
]


async def initialize():
    for manager in managers:
        await manager.initialize()


async def close():
    for manager in managers:
        await manager.sync()
        await manager.close()
