import asyncio

from tortoise import Tortoise, fields
from tortoise.models import Model

from StarManager.core import enums
from StarManager.core.config import database_config


class AccessLevel(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    access_level = fields.IntField(default=0)
    custom_level_name = fields.CharField(32, null=True)

    class Meta:
        table = "accesslvl"


class CustomAccessLevel(Model):
    id = fields.IntField(primary_key=True)
    chat_id = fields.IntField()
    access_level = fields.IntField()
    name = fields.CharField(32)
    emoji = fields.CharField(10, null=True)
    status = fields.BooleanField(default=True)
    commands = fields.JSONField(default=list)

    class Meta:
        table = "customaccesslvl"


class Warn(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    warns = fields.IntField(default=0)
    last_warns_times = fields.TextField(null=True)
    last_warns_names = fields.TextField(null=True)
    last_warns_dates = fields.TextField(null=True)
    last_warns_causes = fields.TextField(null=True)

    class Meta:
        table = "warn"


class Mute(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    mute = fields.IntField(default=0)
    last_mutes_times = fields.TextField(null=True)
    last_mutes_causes = fields.TextField(null=True)
    last_mutes_names = fields.TextField(null=True)
    last_mutes_dates = fields.TextField(null=True)

    class Meta:
        table = "mute"


class Ban(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    ban = fields.BigIntField(default=0)
    last_bans_times = fields.TextField(null=True)
    last_bans_causes = fields.TextField(null=True)
    last_bans_names = fields.TextField(null=True)
    last_bans_dates = fields.TextField(null=True)

    class Meta:
        table = "ban"


class Messages(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    messages = fields.IntField(default=0)

    class Meta:
        table = "messages"


class Nickname(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    nickname = fields.TextField(null=True)

    class Meta:
        table = "nickname"


class LastMessageDate(Model):
    uid = fields.IntField(default=0)
    chat_id = fields.IntField(default=0, db_index=True)
    last_message = fields.IntField(default=0)

    class Meta:
        table = "lastmessagedate"


class SilenceMode(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)
    activated = fields.BooleanField(default=False)
    allowed = fields.TextField(default="[]")
    allowed_custom = fields.TextField(default="[]")

    class Meta:
        table = "silencemode"


class GPool(Model):
    uid = fields.IntField(default=0, db_index=True)
    chat_id = fields.IntField(default=0, unique=True)

    class Meta:
        table = "gpool"


class ChatGroups(Model):
    uid = fields.IntField(default=0, db_index=True)
    group = fields.TextField(null=True)
    chat_id = fields.IntField(default=0)

    class Meta:
        table = "chatgroups"


class Filters(Model):
    chat_id = fields.IntField(null=True)
    owner_id = fields.IntField(null=True)
    filter = fields.TextField()  # type: ignore

    class Meta:
        table = "filters"


class FilterExceptions(Model):
    owner_id = fields.IntField()
    chat_id = fields.IntField()
    filter = fields.TextField()  # type: ignore

    class Meta:
        table = "filterexceptions"


class FilterSettings(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    punishment = fields.IntField(default=0)

    class Meta:
        table = "filtersettings"


class CMDLevels(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    cmd = fields.TextField(null=True)
    lvl = fields.IntField(default=0)

    class Meta:
        table = "commandlevels"


class Blacklist(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)

    class Meta:
        table = "blacklist"


class Premium(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)
    time = fields.BigIntField(default=0)

    class Meta:
        table = "premium"


class Bonus(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)
    time = fields.BigIntField(default=0)
    streak = fields.IntField(default=0)

    class Meta:
        table = "bonus"


class Settings(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    setting = fields.TextField(null=True)
    pos = fields.BooleanField(null=True)
    pos2 = fields.BooleanField(null=True)
    value = fields.IntField(null=True)
    value2 = fields.TextField(null=True)
    punishment = fields.TextField(null=True)

    class Meta:
        table = "settings"


class Welcome(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)
    msg = fields.TextField(null=True)
    photo = fields.TextField(null=True)
    url = fields.TextField(null=True)
    button_label = fields.TextField(null=True)

    class Meta:
        table = "welcome"


class WelcomeHistory(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)
    cmid = fields.IntField()
    time = fields.BigIntField()

    class Meta:
        table = "welcomehistory"


class JoinedDate(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)
    time = fields.BigIntField(default=0)

    class Meta:
        table = "botjoineddate"


class UserJoinedDate(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    uid = fields.IntField(default=0)
    time = fields.BigIntField(default=0)

    class Meta:
        table = "userjoineddate"


class XP(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)
    xp = fields.FloatField(default=0)
    coins = fields.IntField(default=0)
    coins_limit = fields.IntField(default=0)
    lvl = fields.IntField(default=1)
    league = fields.IntField(default=1)
    lm = fields.BigIntField(default=0)
    lvm = fields.BigIntField(default=0)
    lsm = fields.BigIntField(default=0)

    class Meta:
        table = "xp"


class PremMenu(Model):
    uid = fields.IntField(default=0, db_index=True)
    setting = fields.TextField(null=True)
    pos = fields.IntField(null=True)
    value = fields.TextField(null=True)

    class Meta:
        table = "premmenu"


class Prefixes(Model):
    uid = fields.IntField(default=0, db_index=True)
    prefix = fields.TextField(null=True)

    class Meta:
        table = "prefix"


class AccessNames(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    lvl = fields.IntField(default=0)
    name = fields.TextField(null=True)

    class Meta:
        table = "accessnames"


class Ignore(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    uid = fields.IntField(default=0)

    class Meta:
        table = "ignore"


class ChatLimit(Model):
    chat_id = fields.IntField(default=0, unique=True, db_index=True)
    time = fields.BigIntField(default=0)

    class Meta:
        table = "chatlimit"


class Payments(Model):
    uid = fields.IntField(default=0)
    id = fields.IntField(default=0, db_index=True, unique=True, primary_key=True)
    success = fields.IntField(default=0)

    class Meta:
        table = "payments"


class CMDNames(Model):
    uid = fields.IntField(default=0, db_index=True)
    cmd = fields.TextField(null=True)
    name = fields.TextField(null=True)

    class Meta:
        table = "cmdnames"


class DuelWins(Model):
    uid = fields.IntField(default=0, db_index=True, unique=True)
    wins = fields.IntField(default=0)

    class Meta:
        table = "duelwins"


class Referral(Model):
    chat_id = fields.IntField(default=0)
    uid = fields.IntField(default=0, db_index=True)
    from_id = fields.IntField(default=0)

    class Meta:
        table = "refferal"


class GlobalWarns(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)
    warns = fields.IntField(default=0)
    time = fields.IntField(default=0)

    class Meta:
        table = "globalwarns"


class Reports(Model):
    uid = fields.IntField(default=0, db_index=True)
    id = fields.IntField(default=0, primary_key=True)
    time = fields.BigIntField(default=0)
    report_message_ids = fields.TextField()
    report_text = fields.TextField()
    answered_by = fields.BigIntField(null=True)

    class Meta:
        table = "reports"


class Comments(Model):
    uid = fields.IntField(default=0, db_index=True)
    time = fields.BigIntField(default=0)

    class Meta:
        table = "comments"


class Likes(Model):
    uid = fields.IntField(default=0, db_index=True)
    post_id = fields.IntField(default=0)

    class Meta:
        table = "likes"


class Blocked(Model):
    uid = fields.IntField(default=0, db_index=True)
    type = fields.TextField()
    reason = fields.TextField(null=True)

    class Meta:
        table = "blocked"


class Notifs(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    tag = fields.IntField(default=0)
    every = fields.IntField(default=0)
    status = fields.IntField(default=0)
    time = fields.BigIntField(default=0)
    name = fields.TextField(null=True)
    description = fields.TextField(null=True)
    text = fields.TextField(null=True)

    class Meta:
        table = "notifications"


class TypeQueue(Model):
    chat_id = fields.IntField(default=0)
    uid = fields.IntField(default=0, db_index=True)
    type = fields.TextField(null=True)
    additional = fields.TextField(null=True)

    class Meta:
        table = "typequeue"


class ReportBans(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)
    time = fields.BigIntField(null=True)

    class Meta:
        table = "reportban"


class Reboot(Model):
    chat_id = fields.IntField(default=0, db_index=True)
    time = fields.BigIntField(default=0)
    sended = fields.BooleanField(default=0)

    class Meta:
        table = "reboots"


class AllChats(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)

    class Meta:
        table = "allchats"


class AllUsers(Model):
    uid = fields.IntField(default=0, db_index=True, unique=True)
    is_last_hidden_album = fields.BooleanField(default=False)

    class Meta:
        table = "allusers"


class UserNames(Model):
    uid = fields.IntField(default=0, db_index=True, unique=True)
    name = fields.TextField()
    domain = fields.TextField(null=True)

    class Meta:
        table = "usernames"


class ChatNames(Model):
    chat_id = fields.IntField(default=0, db_index=True, unique=True)
    name = fields.TextField()

    class Meta:
        table = "chatnames"


class GroupNames(Model):
    group_id = fields.IntField(default=0, db_index=True, unique=True)
    name = fields.TextField()

    class Meta:
        table = "groupnames"


class TransferHistory(Model):
    to_id = fields.IntField(default=0, db_index=True)
    from_id = fields.IntField(default=0)
    time = fields.BigIntField(default=0)
    amount = fields.IntField(default=0)
    com = fields.IntField(default=0)

    class Meta:
        table = "transferhistory"


class LvlBanned(Model):
    uid = fields.IntField(default=0, unique=True, db_index=True)

    class Meta:
        table = "lvlbanned"


class BotMessages(Model):
    key = fields.CharField(100, unique=True, db_index=True)
    text = fields.TextField()

    class Meta:
        table = "botmessages"


class AnonMessages(Model):
    fromid = fields.IntField()
    chat_id = fields.IntField()
    time = fields.BigIntField()

    class Meta:
        table = "anonmessages"


class AntispamURLExceptions(Model):
    chat_id = fields.IntField()
    url = fields.TextField()

    class Meta:
        table = "antispamurlexceptions"


class CommandsStatistics(Model):
    cmd = fields.TextField()
    timestart = fields.DatetimeField(null=True)
    timeend = fields.DatetimeField(null=True)

    class Meta:
        table = "commandsstatistics"


class MessagesStatistics(Model):
    timestart = fields.DatetimeField(null=True)
    timeend = fields.DatetimeField(null=True)

    class Meta:
        table = "messagesstatistics"


class Captcha(Model):
    chat_id = fields.IntField(db_index=True)
    uid = fields.IntField()
    result = fields.TextField(null=True)
    exptime = fields.BigIntField()
    cmid = fields.IntField(null=True)

    class Meta:
        table = "captcha"


class PublicChats(Model):
    chat_id = fields.IntField(db_index=True, unique=True)
    premium = fields.BooleanField()
    last_up = fields.BigIntField(default=0)
    isopen = fields.BooleanField(default=False)
    members_count = fields.IntField(default=0)

    class Meta:
        table = "publicchats"


class TelegramLink(Model):
    tgid = fields.BigIntField(db_index=True, unique=True, null=True)
    vkid = fields.IntField()
    code = fields.TextField()

    class Meta:
        table = "tglink"


class TGGiveaways(Model):
    mid = fields.BigIntField()

    class Meta:
        table = "tggiveaways"


class TGGiveawayUsers(Model):
    tgid = fields.BigIntField(unique=True)

    class Meta:
        table = "tggiveawayusers"


class TGReferrals(Model):
    fromtgid = fields.BigIntField(db_index=True)
    tgid = fields.BigIntField()

    class Meta:
        table = "tgreferrals"


class TGWaitingForSubscription(Model):
    tgid = fields.BigIntField(db_index=True, unique=True)

    class Meta:
        table = "tgwaitingforsubscription"


class Antitag(Model):
    uid = fields.IntField()
    chat_id = fields.IntField()

    class Meta:
        table = "antitag"


class HiddenAlbumServerInternalError(Model):
    uid = fields.IntField()

    class Meta:
        table = "hiddenalbumserverinternalerror"


class Promocodes(Model):
    code = fields.CharField(255, unique=True, db_index=True)
    usage = fields.IntField(null=True)
    date = fields.IntField(null=True)
    amnt = fields.IntField()
    type = fields.TextField(default="xp")
    sub_needed = fields.BooleanField(default=False)

    class Meta:
        table = "promocodes"


class PromocodeUses(Model):
    code = fields.TextField()
    uid = fields.IntField()

    class Meta:
        table = "promocodeuses"


class ImportSettings(Model):
    uid = fields.IntField()
    chat_id = fields.IntField()
    sys = fields.BooleanField(default=True)
    acc = fields.BooleanField(default=True)
    nicks = fields.BooleanField(default=True)
    punishes = fields.BooleanField(default=True)
    binds = fields.BooleanField(default=False)

    class Meta:
        table = "importsettings"


class NewPostComments(Model):
    uid = fields.IntField()
    pid = fields.IntField()

    class Meta:
        table = "newpostcomments"


class Reputation(Model):
    uid = fields.IntField()
    rep = fields.IntField()

    class Meta:
        table = "reputation"


class RepHistory(Model):
    uid = fields.IntField()
    id = fields.IntField(primary_key=True)
    time = fields.BigIntField()

    class Meta:
        table = "rephistory"


class ReferralBonus(Model):
    chat_id = fields.IntField(db_index=True, unique=True)

    class Meta:
        table = "referralbonus"


class ReferralBonusHistory(Model):
    chat_id = fields.IntField()
    uid = fields.IntField()
    from_id = fields.IntField()

    class Meta:
        table = "referralbonushistory"


class PremPromo(Model):
    promo = fields.TextField()
    val = fields.IntField()
    start = fields.BigIntField()
    end = fields.BigIntField()
    uid = fields.IntField(null=True)  # assigned to

    class Meta:
        table = "prempromo"


class PremiumExpireNotified(Model):
    date = fields.BigIntField()
    uid = fields.IntField()
    cmid = fields.IntField()

    class Meta:
        table = "premiumexpirenotified"


class PaymentHistory(Model):
    uid = fields.IntField()
    pid = fields.IntField()
    date = fields.BigIntField()
    type = fields.TextField()
    sum = fields.IntField()
    comment = fields.TextField()

    class Meta:
        table = "paymenthistory"


class MathGiveaway(Model):
    math = fields.TextField()
    level = fields.IntField()
    cmid = fields.IntField()
    ans = fields.IntField()
    xp = fields.IntField()
    winner = fields.IntField(null=True)
    finished = fields.BooleanField(default=False)

    class Meta:
        table = "mathgiveaway"


class ToDelete(Model):
    peerid = fields.IntField()
    cmid = fields.IntField()
    delete_at = fields.BigIntField()

    class Meta:
        table = "todelete"


class VkLinksExceptions(Model):
    chat_id = fields.IntField(db_index=True)
    url = fields.TextField()

    class Meta:
        table = "vklinksexceptions"


class ForwardedsExceptions(Model):
    chat_id = fields.IntField(db_index=True)
    exc_id = fields.IntField()

    class Meta:
        table = "forwardedsexceptions"


class RewardsCollected(Model):
    uid = fields.IntField(unique=True)
    date = fields.BigIntField()
    deactivated = fields.BooleanField(default=False)

    class Meta:
        table = "rewardscollected"


class Shop(Model):
    uid = fields.IntField(unique=True)
    limits = fields.TextField(default="[0, 0, 0, 0, 0]")
    exp_2x = fields.BigIntField(default=0)
    no_comission = fields.BigIntField(default=0)

    class Meta:
        table = "shop"


class RaidMode(Model):
    chat_id = fields.IntField(unique=True)
    status = fields.BooleanField(default=False)
    trigger_status = fields.BooleanField(default=False)
    limit_invites = fields.IntField(default=5)
    limit_seconds = fields.IntField(default=60)

    class Meta:
        table = "raidmode"


class ChatUserCMIDs(Model):  # questionable solution, looking for a new one
    chat_id = fields.IntField()
    uid = fields.IntField()
    cmid = fields.IntField()

    class Meta:
        table = "chatusercmids"


class UpCommandLogs(Model):
    chat_id = fields.IntField()
    uid = fields.IntField()
    timestamp = fields.BigIntField()

    class Meta:
        table = "upcommandlogs"


class EventTasks(Model):
    uid = fields.IntField(unique=True)
    send_messages = fields.IntField(default=25)
    send_messages_base = fields.IntField(default=25)
    transfer_coins = fields.IntField(default=50)
    transfer_coins_base = fields.IntField(default=50)
    rep_users = fields.IntField(default=3)
    rep_users_base = fields.IntField(default=3)
    win_duels = fields.IntField(default=3)
    win_duels_base = fields.IntField(default=3)
    level_up = fields.IntField(default=1)
    level_up_base = fields.IntField(default=1)
    recieved_case = fields.BooleanField(default=False)

    class Meta:
        table = "eventtasks"


class EventUsers(Model):
    uid = fields.IntField(unique=True)
    cases_opened = fields.IntField(default=0)
    has_cases = fields.IntField(default=0)

    class Meta:
        table = "eventusers"


class RewardsPool(Model):
    uid = fields.IntField()
    reward_category = fields.CharEnumField(enums.RewardCategory)
    value = fields.IntField()

    class Meta:
        table = "rewardspool"


async def init() -> None:
    await Tortoise.init(config=database_config)
    await Tortoise.generate_schemas()


if __name__ == "__main__":
    asyncio.run(init())
