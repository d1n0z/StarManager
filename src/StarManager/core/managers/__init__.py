from .access_level import AccessLevelManager
from .allchats import AllChatsManager
from .allusers import AllUsersManager
from .antispam_messages import AntispamMessagesManager
from .chat_settings import ChatSettingsManager
from .chatusercmids import ChatUserCMIDsManager
from .cmdnames import CommandNamesManager
from .commands_cooldown import CommandsCooldownManager
from .custom_access_level import CustomAccessLevelManager
from .duel import DuelLockManager
from .event import EventManager
from .filters import FiltersManager
from .prefix import PrefixesManager
from .public_chats import PublicChatsManager
from .punishments import BanManager, MuteManager, WarnManager
from .raid import RaidManager
from .rps import RPSManager
from .xp import XPManager

managers = [
    access_level := AccessLevelManager(),
    allchats := AllChatsManager(),
    allusers := AllUsersManager(),
    antispam := AntispamMessagesManager(),
    chat_settings := ChatSettingsManager(),
    chat_user_cmids := ChatUserCMIDsManager(),
    cmdnames := CommandNamesManager(),
    commands_cooldown := CommandsCooldownManager(),
    custom_access_level := CustomAccessLevelManager(),
    duel_lock := DuelLockManager(),
    event := EventManager(),
    filters := FiltersManager(),
    prefixes := PrefixesManager(),
    public_chats := PublicChatsManager(),
    ban := BanManager(),
    mute := MuteManager(),
    warn := WarnManager(),
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
