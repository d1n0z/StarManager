from .access_level import AccessLevelManager
from .antispam_messages import AntispamMessagesManager
from .chat_settings import ChatSettingsManager
from .chatusercmids import ChatUserCMIDsManager
from .commands_cooldown import CommandsCooldownManager
from .custom_access_level import CustomAccessLevelManager
from .duel import DuelLockManager
from .public_chats import PublicChatsManager
from .raid import RaidManager
from .rps import RPSManager
from .xp import XPManager

managers = [
    access_level := AccessLevelManager(),
    antispam := AntispamMessagesManager(),
    chat_settings := ChatSettingsManager(),
    chat_user_cmids := ChatUserCMIDsManager(),
    commands_cooldown := CommandsCooldownManager(),
    custom_access_level := CustomAccessLevelManager(),
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
