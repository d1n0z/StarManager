from datetime import datetime

from peewee import PostgresqlDatabase, Model, IntegerField, BigIntegerField, TextField, BooleanField, TimestampField, \
    DateTimeField
from config.config import USER, PASSWORD, DATABASE

dbhandle = PostgresqlDatabase(DATABASE, user=USER, password=PASSWORD, host='localhost')


class AccessLevel(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    access_level = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = 'accesslvl'


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
        db_table = 'warn'


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
        db_table = 'mute'


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
        db_table = 'ban'


class Messages(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    messages = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = 'messages'


class Nickname(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    nickname = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = 'nickname'


class LastMessageDate(Model):
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0, index=True)
    last_message = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = 'lastmessagedate'


class SilenceMode(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'silencemode'


class GPool(Model):
    uid = IntegerField(default=0, index=True)
    chat_id = IntegerField(default=0, unique=True)

    class Meta:
        database = dbhandle
        db_table = f'gpool'


class ChatGroups(Model):
    uid = IntegerField(default=0, index=True)
    group = TextField(null=True)
    chat_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'chatgroups'


class Filters(Model):
    chat_id = IntegerField(default=0, index=True)
    filter = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'filters'


class CMDLevels(Model):
    chat_id = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    lvl = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'commandlevels'


class Blacklist(Model):
    uid = IntegerField(default=0, unique=True, index=True)

    class Meta:
        database = dbhandle
        db_table = f'blacklist'


class Premium(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'premium'


class Bonus(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'bonus'


class Settings(Model):
    chat_id = IntegerField(default=0, index=True)
    setting = TextField(null=True)
    pos = BooleanField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'settings'


class Welcome(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    msg = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'welcome'


class JoinedDate(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'botjoineddate'


class UserJoinedDate(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'userjoineddate'


class XP(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    xp = IntegerField(default=0)
    lm = BigIntegerField()

    class Meta:
        database = dbhandle
        db_table = f'xp'


class PremMenu(Model):
    uid = IntegerField(default=0, index=True)
    setting = TextField(null=True)
    pos = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'premmenu'


class Prefixes(Model):
    uid = IntegerField(default=0, index=True)
    prefix = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'prefix'


class AccessNames(Model):
    chat_id = IntegerField(default=0, index=True)
    lvl = IntegerField(default=0)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'accessnames'


class Ignore(Model):
    chat_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'ignore'


class ChatLimit(Model):
    chat_id = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'chatlimit'


class Payments(Model):
    uid = IntegerField(default=0)
    id = IntegerField(default=0, index=True, unique=True)
    success = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'payments'


class CMDNames(Model):
    uid = IntegerField(default=0, index=True)
    cmd = TextField(null=True)
    name = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'cmdnames'


class DuelWins(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    wins = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'duelwins'


class Referral(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'refferal'


class LastFiveCommands(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    cmds = TextField(null=True)
    cmd_time = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'lastfivecommands'


class GlobalWarns(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    warns = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'globalwarns'


class Reports(Model):
    uid = IntegerField(default=0, index=True)
    id = IntegerField(default=0)
    time = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'reports'


class ReportAnswers(Model):
    answering_id = IntegerField(default=0, index=True)
    uid = IntegerField(default=0)
    chat_id = IntegerField(default=0)
    repid = IntegerField(default=0, unique=True)
    report_text = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'reportanswers'


class Comments(Model):
    uid = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'comments'


class Likes(Model):
    uid = IntegerField(default=0, index=True)
    post_id = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'likes'


class InfBanned(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    type = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'infbanned'


class LeavedChats(Model):
    chat_id = IntegerField(default=0, unique=True, index=True)
    time = BigIntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'leavedchats'


class CompletedRewards(Model):
    uid = IntegerField(default=0, index=True)
    type = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'completedrewards'


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
        db_table = f'notifications'


class TypeQueue(Model):
    chat_id = IntegerField(default=0)
    uid = IntegerField(default=0, index=True)
    type = TextField(null=True)
    additional = TextField(null=True)

    class Meta:
        database = dbhandle
        db_table = f'typequeue'


class ReportWarns(Model):
    uid = IntegerField(default=0, unique=True, index=True)
    warns = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'reportwarns'


class Reboot(Model):
    chat_id = IntegerField(default=0, index=True)
    time = BigIntegerField(default=0)
    sended = BooleanField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'reboots'


class AllChats(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)

    class Meta:
        database = dbhandle
        db_table = f'allchats'


class AllUsers(Model):
    uid = IntegerField(default=0, index=True, unique=True)

    class Meta:
        database = dbhandle
        db_table = f'allusers'


class UserNames(Model):
    uid = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        db_table = f'usernames'


class ChatNames(Model):
    chat_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        db_table = f'chatnames'


class GroupNames(Model):
    group_id = IntegerField(default=0, index=True, unique=True)
    name = TextField()

    class Meta:
        database = dbhandle
        db_table = f'groupnames'


class TasksDaily(Model):
    uid = IntegerField(default=0, index=True)
    task = TextField()
    count = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'tasksdaily'


class TasksWeekly(Model):
    uid = IntegerField(default=0, index=True)
    task = TextField()
    count = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'tasksweekly'


class Coins(Model):
    uid = IntegerField(default=0, index=True)
    coins = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'coins'


class TasksStreak(Model):
    uid = IntegerField(default=0, index=True)
    streak = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'tasksstreak'


class TransferHistory(Model):
    to_id = IntegerField(default=0, index=True)
    from_id = IntegerField(default=0)
    time = BigIntegerField(default=0)
    amount = IntegerField(default=0)
    com = IntegerField(default=0)

    class Meta:
        database = dbhandle
        db_table = f'transferhistory'


class MessagesHistory(Model):
    cmid = IntegerField(default=0, index=True)
    id = IntegerField(default=0)
    chat_id = IntegerField()
    from_id = IntegerField()
    text = TextField()
    time = BigIntegerField()

    class Meta:
        database = dbhandle
        db_table = f'messageshistory'
