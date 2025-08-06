from peewee import (PostgresqlDatabase, Model, IntegerField, BigIntegerField, TextField, BooleanField, DateTimeField,
                    FloatField)
from config.config import USER, PASSWORD, DATABASE, DATABASE_PORT, DATABASE_HOST

dbhandle = PostgresqlDatabase(DATABASE, user=USER, password=PASSWORD, host=DATABASE_HOST, port=DATABASE_PORT)
# TODO: remove default=0 where not needed


class AccessLevel(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    access_level = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'accesslvl'


class Warn(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    warns = IntegerField(default=0)
    last_warns_times = TextField(null=True)
    last_warns_names = TextField(null=True)
    last_warns_dates = TextField(null=True)
    last_warns_causes = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'warn'


class Mute(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    mute = IntegerField(default=0)
    last_mutes_times = TextField(null=True)
    last_mutes_causes = TextField(null=True)
    last_mutes_names = TextField(null=True)
    last_mutes_dates = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'mute'


class Ban(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    ban = BigIntegerField(default=0)
    last_bans_times = TextField(null=True)
    last_bans_causes = TextField(null=True)
    last_bans_names = TextField(null=True)
    last_bans_dates = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'ban'


class Messages(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    messages = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'messages'


class Nickname(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    nickname = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'nickname'


class LastMessageDate(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    last_message = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'lastmessagedate'


class SilenceMode(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    activated = BooleanField(default=False)
    allowed = TextField(default='[]')

    class Meta:
        database = dbhandle
        table_name = 'silencemode'


class GPool(Model):
    uid = IntegerField(default=0, index=True)
    chat_id = IntegerField(default=0, unique=True)

    class Meta:
        database = dbhandle
        table_name = 'gpool'


class ChatGroups(Model):
    uid = IntegerField(default=0, index=True)
    group = TextField(null=True)
    chat_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'chatgroups'


class Filters(Model):
    chat_id = IntegerField(null=True)
    owner_id = IntegerField(null=True)
    filter = TextField()

    class Meta:
        database = dbhandle
        table_name = 'filters'


class FilterExceptions(Model):
    owner_id = IntegerField()
    chat_id = IntegerField()
    filter = TextField()

    class Meta:
        database = dbhandle
        table_name = 'filterexceptions'


class FilterSettings(Model):
    chat_id = IntegerField(default=0, index=True)
    punishment = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'filtersettings'


class CMDLevels(Model):
    chat_id = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    lvl = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'commandlevels'


class Blacklist(Model):
    uid = IntegerField(default=0, unique=True, index=True)

    class Meta:
        database = dbhandle
        table_name = 'blacklist'


class Premium(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'premium'


class Bonus(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)
    streak = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'bonus'


class Settings(Model):
    chat_id = IntegerField(default=0, index=True)
    setting = TextField(null=True)
    pos = BooleanField(null=True)
    pos2 = BooleanField(null=True)
    value = IntegerField(null=True)
    value2 = TextField(null=True)
    punishment = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'settings'


class Welcome(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    msg = TextField(null=True)
    photo = TextField(null=True)
    url = TextField(null=True)
    button_label = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'welcome'


class WelcomeHistory(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    cmid = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'welcomehistory'


class JoinedDate(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'botjoineddate'


class UserJoinedDate(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    time = BigIntegerField(default=0)

    class Meta:
        table_name = 'userjoineddate'
        database = dbhandle


class XP(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    xp = FloatField(default=0)
    coins = IntegerField(default=0)
    coins_limit = IntegerField(default=0)
    lvl = IntegerField(default=1)
    league = IntegerField(default=1)
    lm = BigIntegerField(default=0)
    lvm = BigIntegerField(default=0)
    lsm = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'xp'


class PremMenu(Model):
    uid = IntegerField(default=0, index=True)
    setting = TextField(null=True)
    pos = IntegerField(null=True)
    value = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'premmenu'


class Prefixes(Model):
    uid = IntegerField(default=0, index=True)
    prefix = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'prefix'


class AccessNames(Model):
    chat_id = IntegerField(default=0, index=True)
    lvl = IntegerField(default=0)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'accessnames'


class Ignore(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'ignore'


class ChatLimit(Model):
    chat_id = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'chatlimit'


class Payments(Model):
    uid = IntegerField(default=0)
    id = IntegerField(default=0, index=True, unique=True)
    success = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'payments'


class CMDNames(Model):
    uid = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'cmdnames'


class DuelWins(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    wins = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'duelwins'


class Referral(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'refferal'


class GlobalWarns(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    warns = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'globalwarns'


class Reports(Model):
    uid = IntegerField(default=0, index=True)
    id = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'reports'


class ReportAnswers(Model):
    answering_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0)
    repid = IntegerField(default=0, unique=True)
    report_text = TextField(null=True)
    cmid = IntegerField(null=True)
    photos = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'reportanswers'


class Comments(Model):
    uid = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'comments'


class Likes(Model):
    uid = IntegerField(default=0, index=True)
    post_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'likes'


class Blocked(Model):
    uid = IntegerField(default=0, index=True)
    type = TextField()
    reason = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'blocked'


class Notifs(Model):
    chat_id = IntegerField(default=0, index=True)
    tag = IntegerField(default=0)
    every = IntegerField(default=0)
    status = IntegerField(default=0)
    time = BigIntegerField(default=0)
    name = TextField(null=True)
    description = TextField(null=True)
    text = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'notifications'


class TypeQueue(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    type = TextField(null=True)
    additional = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'typequeue'


class ReportBans(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'reportban'


class Reboot(Model):
    chat_id = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)
    sended = BooleanField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'reboots'


class AllChats(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)

    class Meta:
        database = dbhandle
        table_name = 'allchats'


class AllUsers(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    is_last_hidden_album = BooleanField(default=False)

    class Meta:
        database = dbhandle
        table_name = 'allusers'


class UserNames(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = 'usernames'


class ChatNames(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = 'chatnames'


class GroupNames(Model):
    group_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = 'groupnames'


class TransferHistory(Model):
    to_id = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)
    time = BigIntegerField(default=0)
    amount = IntegerField(default=0)
    com = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'transferhistory'


class LvlBanned(Model):
    uid = IntegerField(default=0, unique=True, index=True)

    class Meta:
        database = dbhandle
        table_name = 'lvlbanned'


class BotMessages(Model):
    key = TextField(unique=True, index=True)
    text = TextField()

    class Meta:
        database = dbhandle
        table_name = 'botmessages'


class AnonMessages(Model):
    fromid = IntegerField()
    chat_id = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'anonmessages'


class AntispamURLExceptions(Model):
    chat_id = IntegerField()
    url = TextField()

    class Meta:
        database = dbhandle
        table_name = 'antispamurlexceptions'


class CommandsStatistics(Model):
    cmd = TextField()
    timestart = DateTimeField(null=True)
    timeend = DateTimeField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'commandsstatistics'


class MessagesStatistics(Model):
    timestart = DateTimeField(null=True)
    timeend = DateTimeField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'messagesstatistics'


class Captcha(Model):
    chat_id = IntegerField(index=True)
    uid = IntegerField()
    result = TextField(null=True)
    exptime = BigIntegerField()
    cmid = IntegerField(null=True)

    class Meta:
        database = dbhandle
        table_name = 'captcha'


class PublicChats(Model):
    chat_id = IntegerField(index=True, unique=True)
    premium = BooleanField()
    isopen = BooleanField(default=False)

    class Meta:
        database = dbhandle
        table_name = 'publicchats'


class PublicChatsSettings(Model):
    chat_id = IntegerField(index=True, unique=True)
    link = TextField()
    photo = TextField()
    name = TextField()
    members = IntegerField()
    last_update = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'publicchatssettings'


class TelegramLink(Model):
    tgid = BigIntegerField(index=True, unique=True, null=True)
    vkid = IntegerField()
    code = TextField()

    class Meta:
        database = dbhandle
        table_name = 'tglink'


class TGGiveaways(Model):
    mid = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'tggiveaways'


class TGGiveawayUsers(Model):
    tgid = BigIntegerField(unique=True)

    class Meta:
        database = dbhandle
        table_name = 'tggiveawayusers'


class TGReferrals(Model):
    fromtgid = BigIntegerField(index=True)
    tgid = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'tgreferrals'


class TGWaitingForSubscription(Model):
    tgid = BigIntegerField(index=True, unique=True)

    class Meta:
        database = dbhandle
        table_name = 'tgwaitingforsubscription'


class CommandsUsage(Model):
    uid = IntegerField()
    cmd = TextField(index=True)

    class Meta:
        database = dbhandle
        table_name = 'cmdsusage'


class Antitag(Model):
    uid = IntegerField()
    chat_id = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'antitag'


class HiddenAlbumServerInternalError(Model):
    uid = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'hiddenalbumserverinternalerror'


class Promocodes(Model):
    code = TextField(unique=True, index=True)
    usage = IntegerField(null=True)
    date = IntegerField(null=True)
    amnt = IntegerField()
    type = TextField(default='xp')

    class Meta:
        database = dbhandle
        table_name = 'promocodes'


class PromocodeUses(Model):
    code = TextField()
    uid = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'promocodeuses'


class ImportSettings(Model):
    uid = IntegerField()
    chat_id = IntegerField()
    sys = BooleanField(default=True)
    acc = BooleanField(default=True)
    nicks = BooleanField(default=True)
    punishes = BooleanField(default=True)
    binds = BooleanField(default=False)

    class Meta:
        database = dbhandle
        table_name = 'importsettings'


class NewPostComments(Model):
    uid = IntegerField()
    pid = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'newpostcomments'


class Reputation(Model):
    uid = IntegerField()
    rep = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'reputation'


class RepHistory(Model):
    uid = IntegerField()
    id = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'rephistory'


class ReferralBonus(Model):
    chat_id = IntegerField(index=True, unique=True)

    class Meta:
        database = dbhandle
        table_name = 'referralbonus'


class ReferralBonusHistory(Model):
    chat_id = IntegerField()
    uid = IntegerField()
    from_id = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'referralbonushistory'


class PremPromo(Model):
    promo = TextField()
    val = IntegerField()
    start = BigIntegerField()
    end = BigIntegerField()
    uid = IntegerField(null=True)  # assigned to

    class Meta:
        database = dbhandle
        table_name = 'prempromo'


class PremiumExpireNotified(Model):
    date = BigIntegerField()
    uid = IntegerField()
    cmid = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'premiumexpirenotified'


class PaymentHistory(Model):
    uid = IntegerField()
    pid = IntegerField()
    date = BigIntegerField()
    type = TextField()
    sum = IntegerField()
    comment = TextField()

    class Meta:
        database = dbhandle
        table_name = 'paymenthistory'


class MathGiveaway(Model):
    math = TextField()
    level = IntegerField()
    cmid = IntegerField()
    ans = IntegerField()
    xp = IntegerField()
    winner = IntegerField(null=True)
    finished = BooleanField(default=False)

    class Meta:
        database = dbhandle
        table_name = 'mathgiveaway'


class ToDelete(Model):
    peerid = IntegerField()
    cmid = IntegerField()
    delete_at = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = 'todelete'


class VkLinksExceptions(Model):
    chat_id = IntegerField(index=True)
    url = TextField()

    class Meta:
        database = dbhandle
        table_name = 'vklinksexceptions'


class ForwardedsExceptions(Model):
    chat_id = IntegerField(index=True)
    exc_id = IntegerField()

    class Meta:
        database = dbhandle
        table_name = 'forwardedsexceptions'


class RewardsCollected(Model):
    uid = IntegerField(unique=True)
    date = BigIntegerField()
    deactivated = BooleanField(default=False)

    class Meta:
        database = dbhandle
        table_name = 'rewardscollected'


class Shop(Model):
    uid = IntegerField(unique=True)
    limits = TextField(default='[0, 0, 0, 0, 0]')
    exp_2x = BigIntegerField(default=0)
    no_comission = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = 'shop'


if __name__ == '__main__':
    dbhandle.create_tables(Model.__subclasses__())
