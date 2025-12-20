from enum import Enum


class RPSPick(str, Enum):
    r = "камень"
    p = "бумага"
    s = "ножницы"


class ChatsMode(str, Enum):
    all = "all"
    premium = "premium"


class RewardCategory(str, Enum):
    premium = "Premium"
    coins = "Coins"
    xp = "Experience"
    money = "Money"


class TaskCategory(str, Enum):
    send_messages = "send_messages"
    transfer_coins = "transfer_coins"
    rep_users = "rep_users"
    win_duels = "win_duels"
    level_up = "level_up"
