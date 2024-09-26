from peewee import PostgresqlDatabase, Model, IntegerField, BigIntegerField, TextField, BooleanField, DateTimeField
from config.config import USER, PASSWORD, DATABASE

dbhandle = PostgresqlDatabase(DATABASE, user=USER, password=PASSWORD, host='localhost')


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
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'silencemode'


class GPool(Model):
    uid = IntegerField(default=0, index=True)
    chat_id = IntegerField(default=0, unique=True)

    class Meta:
        database = dbhandle
        table_name = f'gpool'


class ChatGroups(Model):
    uid = IntegerField(default=0, index=True)
    group = TextField(null=True)
    chat_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'chatgroups'


class Filters(Model):
    chat_id = IntegerField(default=0, index=True)
    filter = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'filters'


class CMDLevels(Model):
    chat_id = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    lvl = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'commandlevels'


class Blacklist(Model):
    uid = IntegerField(default=0, unique=True, index=True)

    class Meta:
        database = dbhandle
        table_name = f'blacklist'


class Premium(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'premium'


class Bonus(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'bonus'


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
        table_name = f'settings'


class Welcome(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    msg = TextField(null=True)
    photo = TextField(null=True)
    url = TextField(null=True)
    button_label = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'welcome'


class WelcomeHistory(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    cmid = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'welcomehistory'


class JoinedDate(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'botjoineddate'


class UserJoinedDate(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'userjoineddate'


class XP(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    xp = IntegerField(default=0)
    lm = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'xp'


class PremMenu(Model):
    uid = IntegerField(default=0, index=True)
    setting = TextField(null=True)
    pos = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'premmenu'


class Prefixes(Model):
    uid = IntegerField(default=0, index=True)
    prefix = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'prefix'


class AccessNames(Model):
    chat_id = IntegerField(default=0, index=True)
    lvl = IntegerField(default=0)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'accessnames'


class Ignore(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'ignore'


class ChatLimit(Model):
    chat_id = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'chatlimit'


class Payments(Model):
    uid = IntegerField(default=0)
    id = IntegerField(default=0, index=True, unique=True)
    success = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'payments'


class CMDNames(Model):
    uid = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'cmdnames'


class DuelWins(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    wins = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'duelwins'


class Referral(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'refferal'


class LastFiveCommands(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    cmds = TextField(null=True)
    cmd_time = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'lastfivecommands'


class GlobalWarns(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    warns = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'globalwarns'


class Reports(Model):
    uid = IntegerField(default=0, index=True)
    id = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'reports'


class ReportAnswers(Model):
    answering_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0)
    repid = IntegerField(default=0, unique=True)
    report_text = TextField(null=True)
    cmid = IntegerField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'reportanswers'


class Comments(Model):
    uid = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'comments'


class Likes(Model):
    uid = IntegerField(default=0, index=True)
    post_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'likes'


class InfBanned(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    type = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'infbanned'


class LeavedChats(Model):
    chat_id = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'leavedchats'


class CompletedRewards(Model):
    uid = IntegerField(default=0, index=True)
    type = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'completedrewards'


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
        table_name = f'notifications'


class TypeQueue(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    type = TextField(null=True)
    additional = TextField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'typequeue'


class ReportWarns(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    warns = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'reportwarns'


class Reboot(Model):
    chat_id = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)
    sended = BooleanField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'reboots'


class AllChats(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)

    class Meta:
        database = dbhandle
        table_name = f'allchats'


class AllUsers(Model):
    uid = IntegerField(default=0, index=True, unique=True)

    class Meta:
        database = dbhandle
        table_name = f'allusers'


class UserNames(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = f'usernames'


class ChatNames(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = f'chatnames'


class GroupNames(Model):
    group_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        table_name = f'groupnames'


class TasksDaily(Model):
    uid = IntegerField(default=0, index=True)
    task = TextField()
    count = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'tasksdaily'


class TasksWeekly(Model):
    uid = IntegerField(default=0, index=True)
    task = TextField()
    count = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'tasksweekly'


class Coins(Model):
    uid = IntegerField(default=0, index=True)
    coins = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'coins'


class TasksStreak(Model):
    uid = IntegerField(default=0, index=True)
    streak = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'tasksstreak'


class TransferHistory(Model):
    to_id = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)
    time = BigIntegerField(default=0)
    amount = IntegerField(default=0)
    com = IntegerField(default=0)

    class Meta:
        database = dbhandle
        table_name = f'transferhistory'


class MessagesHistory(Model):  # unused
    cmid = IntegerField(default=0, index=True)
    id = IntegerField(default=0)
    chat_id = IntegerField()
    from_id = IntegerField()
    text = TextField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'messageshistory'


class LvlBanned(Model):
    uid = IntegerField(default=0, unique=True, index=True)

    class Meta:
        database = dbhandle
        table_name = f'lvlbanned'


class BotMessages(Model):
    key = TextField(unique=True, index=True)
    text = TextField()

    class Meta:
        database = dbhandle
        table_name = f'botmessages'


class AnonMessages(Model):
    fromid = IntegerField()
    chat_id = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'anonmessages'


class AntispamMessages(Model):
    cmid = IntegerField(default=0)
    chat_id = IntegerField()
    from_id = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'antispammessages'


class AntispamURLExceptions(Model):
    chat_id = IntegerField()
    url = TextField()

    class Meta:
        database = dbhandle
        table_name = f'antispamurlexceptions'


class SpecCommandsCooldown(Model):
    uid = IntegerField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        table_name = f'speccommandscooldown'


class CommandsStatistics(Model):
    cmd = TextField()
    timestart = DateTimeField(null=True)
    timeend = DateTimeField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'commandsstatistics'


class MessagesStatistics(Model):
    timestart = DateTimeField(null=True)
    timeend = DateTimeField(null=True)

    class Meta:
        database = dbhandle
        table_name = f'messagesstatistics'
