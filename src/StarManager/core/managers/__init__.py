from .access_level import AccessLevelManager
from .allchats import AllChatsManager
from .allusers import AllUsersManager
from .antispam_messages import AntispamMessagesManager
from .antitag import AntitagManager
from .blocked import BlockedManager
from .chat_settings import ChatSettingsManager
from .chatlimit import ChatLimitManager
from .chatusercmids import ChatUserCMIDsManager
from .cmdnames import CommandNamesManager
from .commands_cooldown import CommandsCooldownManager
from .custom_access_level import CustomAccessLevelManager
from .duel import DuelLockManager
from .event import EventManager
from .filters import FiltersManager
from .lastmessagedate import LastMessageDateManager
from .lvlbanned import LvlBannedManager
from .messages import MessagesManager
from .prefix import PrefixesManager
from .premium import PremiumManager
from .public_chats import PublicChatsManager
from .punishments import BanManager, MuteManager, WarnManager
from .raid import RaidManager
from .rewardscollected import RewardsCollectedManager
from .rps import RPSManager
from .silence import SilenceModeManager
from .xp import XPManager

managers = [
    access_level := AccessLevelManager(),
    allchats := AllChatsManager(),
    allusers := AllUsersManager(),
    antispam := AntispamMessagesManager(),
    antitag := AntitagManager(),
    blocked := BlockedManager(),
    chat_settings := ChatSettingsManager(),
    chatlimit := ChatLimitManager(),
    chat_user_cmids := ChatUserCMIDsManager(),
    cmdnames := CommandNamesManager(),
    commands_cooldown := CommandsCooldownManager(),
    custom_access_level := CustomAccessLevelManager(),
    duel_lock := DuelLockManager(),
    event := EventManager(),
    filters := FiltersManager(),
    lastmessagedate := LastMessageDateManager(),
    lvlbanned := LvlBannedManager(),
    messages := MessagesManager(),
    prefixes := PrefixesManager(),
    premium := PremiumManager(),
    public_chats := PublicChatsManager(),
    ban := BanManager(),
    mute := MuteManager(),
    warn := WarnManager(),
    raid := RaidManager(),
    rewardscollected := RewardsCollectedManager(),
    rps := RPSManager(),
    silencemode := SilenceModeManager(),
    xp := XPManager(),
]


async def initialize():
    for manager in managers:
        await manager.initialize()


async def close():
    for manager in managers:
        await manager.sync()
        await manager.close()
