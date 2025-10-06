from enum import Enum


class RPSPick(str, Enum):
    r = "камень"
    p = "бумага"
    s = "ножницы"


class ChatsMode(str, Enum):
    all = "all"
    premium = "premium"
