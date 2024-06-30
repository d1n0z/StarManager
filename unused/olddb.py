# from peewee import *
# from config.config import *
#
# dbhandle = PostgresqlDatabase(
#     DATABASE, user=USER,
#     password=PASSWORD,
#     host='localhost',
# )
# pdbhandle = PostgresqlDatabase(
#     PFDATABASE, user=USER,
#     password=PASSWORD,
#     host='localhost'
# )
#
#
# def getChat(chat_id, createIfNotExist=True):
#     class Chat(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         access_level = IntegerField(default=0)
#         warns = IntegerField(default=0)
#         mute = IntegerField(default=0)
#         ban = BigIntegerField(default=0)
#         messages = IntegerField(default=0)
#         nickname = TextField(null=True)
#         last_message = IntegerField(default=0)
#         global_warn = SmallIntegerField(default=0)
#         global_warn_cause = TextField(null=True)
#         global_ban = SmallIntegerField(default=0)
#         global_ban_cause = TextField(null=True)
#         premium = SmallIntegerField(default=0)
#         mute_cause = TextField(null=True)
#         last_bans_times = TextField(null=True)
#         last_mutes_times = TextField(null=True)
#         last_warns_times = TextField(null=True)
#         last_bans_causes = TextField(null=True)
#         last_mutes_causes = TextField(null=True)
#         last_warns_causes = TextField(null=True)
#         last_bans_names = TextField(null=True)
#         last_mutes_names = TextField(null=True)
#         last_warns_names = TextField(null=True)
#         last_bans_dates = TextField(null=True)
#         last_mutes_dates = TextField(null=True)
#         last_warns_dates = TextField(null=True)
#         kicked = SmallIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = dbhandle
#             db_table = f'{chat_id}'
#
#     if createIfNotExist:
#         Chat.create_table()
#     return Chat
#
#
# def getSilenceMode():
#     class SilenceMode(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'SILENCE_MODE'
#
#     SilenceMode.create_table()
#     return SilenceMode
#
#
# def getGPool():
#     class GPool(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         chat_id = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'GPOOL'
#
#     GPool.create_table()
#     return GPool
#
#
# def getChatGroups():
#     class ChatGroups(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         group = TextField(null=True)
#         chat_id = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'CHAT_GROUPS'
#
#     ChatGroups.create_table()
#     return ChatGroups
#
#
# def getFilters():
#     class Filters(Model):
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         filter = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'FILTERS'
#
#     Filters.create_table()
#     return Filters
#
#
# def getCommandLevels():
#     class Chat(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         cmd = TextField(null=True)
#         lvl = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'COMMAND_LEVELS'
#
#     Chat.create_table()
#     return Chat
#
#
# def getBlacklist():
#     class Blacklist(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'BLACKLIST'
#
#     Blacklist.create_table()
#     return Blacklist
#
#
# def getPremium():
#     class Premium(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'PREMIUM'
#
#     Premium.create_table()
#     return Premium
#
#
# def getBonus():
#     class Bonus(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'BONUS'
#
#     Bonus.create_table()
#     return Bonus
#
#
# def getSettings():
#     class Settings(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         setting = TextField(null=True)
#         pos = SmallIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'SETTINGS'
#
#     Settings.create_table()
#     return Settings
#
#
# def getJoinedDate():
#     class JoinedDate(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'JoinedDate'
#
#     JoinedDate.create_table()
#     return JoinedDate
#
#
# def getUserJoinedDate():
#     class UserJoinedDate(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         uid = IntegerField(default=0)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'USER_JOINED_DATE'
#
#     UserJoinedDate.create_table()
#     return UserJoinedDate
#
#
# def getLVL():
#     class LVL(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         xp = IntegerField(default=0)
#         lm = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'LVL'
#
#     LVL.create_table()
#     return LVL
#
#
# def getPremMenu():
#     class PremMenu(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         setting = TextField(null=True)
#         pos = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'PREMMENU'
#
#     PremMenu.create_table()
#     return PremMenu
#
#
# def getPrefixes():
#     class Prefixes(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         prefix = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'PREFIXES'
#
#     Prefixes.create_table()
#     return Prefixes
#
#
# def getAccessNames():
#     class AccessNames(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         lvl = IntegerField(default=0)
#         name = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'ACCESS_NAMES'
#
#     AccessNames.create_table()
#     return AccessNames
#
#
# # def getCMDCounter():
# #     class CMDCounter(Model):
# #         """
# #         ORM model of the Chat table
# #         """
# #
# #         cmd = TextField(null=True)
# #         count = IntegerField(default=0)
# #
# #         class Meta:
# #             primary_key = False
# #             database = pdbhandle
# #             db_table = f'CMD_COUNTER'
# #
# #     CMDCounter.create_table()
# #     return CMDCounter
#
#
# def getIgnore():
#     class Ignore(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0)
#         uid = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'IGNORE'
#
#     Ignore.create_table()
#     return Ignore
#
#
# def getChatLimit():
#     class ChatLimit(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         unix_time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'CHATLIMIT'
#
#     ChatLimit.create_table()
#     return ChatLimit
#
#
# def getPayments():
#     class Payments(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0)
#         id = IntegerField(default=0, index=True, unique=True)
#         success = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'PAYMENTS'
#
#     Payments.create_table()
#     return Payments
#
#
# def getCMDNames():
#     class CMDNames(Model):
#         uid = IntegerField(default=0, index=True, unique=True)
#         cmd = TextField(null=True)
#         name = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'CMDNAMES'
#
#     CMDNames.create_table()
#     return CMDNames
#
#
# def getNonce():
#     class Nonce(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         nonce = IntegerField(default=100)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'NONCE'
#
#     Nonce.create_table()
#     try:
#         nonce = Nonce.select().where(Nonce.nonce > 0)[0].nonce
#         Nonce.update(nonce=nonce + 1).execute()
#         return nonce
#     except:
#         Nonce.insert(nonce=100).execute()
#         return 100
#
#
# def getDuelWins():
#     class DuelWins(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         wins = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'DUELWINS'
#
#     DuelWins.create_table()
#     return DuelWins
#
#
# def getDuels():
#     class Duels(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         wins = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'Duels'
#
#     Duels.create_table()
#     return Duels
#
#
# def getReferral():
#     class Referral(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0)
#         uid = IntegerField(default=0)
#         from_id = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REFERRAL'
#
#     Referral.create_table()
#     return Referral
#
#
# def getLastFiveCommands():
#     class LastFiveCommands(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         cmds = TextField(null=True)
#         cmd_time = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'LASTFIVECOMMANDS'
#
#     LastFiveCommands.create_table()
#     return LastFiveCommands
#
#
# def getGlobalWarns():
#     class GlobalWarns(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         warns = IntegerField(default=0)
#         time = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'GLOBALWARNS'
#
#     GlobalWarns.create_table()
#     return GlobalWarns
#
#
# def getReports():
#     class Reports(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         id = IntegerField(default=0)
#         time = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REPORTS'
#
#     Reports.create_table()
#     return Reports
#
#
# def getReportAnswers():
#     class ReportAnswers(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         answering_id = IntegerField(default=0)
#         uid = IntegerField(default=0)
#         chat_id = IntegerField(default=0)
#         repid = IntegerField(default=0)
#         report_text = TextField(null=True, index=True, unique=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REPORTANSWERS'
#
#     ReportAnswers.create_table()
#     return ReportAnswers
#
#
# def getComments():
#     class Comments(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'COMMENTS'
#
#     Comments.create_table()
#     return Comments
#
#
# def getLikes():
#     class Likes(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         post_id = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'LIKES'
#
#     Likes.create_table()
#     return Likes
#
#
# def getInfBanned():
#     class InfBanned(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         type = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'INFBANNED'
#
#     InfBanned.create_table()
#     return InfBanned
#
#
# def getLeavedChats():
#     class LeavedChats(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         id = IntegerField(default=0, index=True, unique=True)
#         time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'LEAVEDCHATS'
#
#     LeavedChats.create_table()
#     return LeavedChats
#
#
# def getRewards():
#     class Rewards(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         type = IntegerField(default=0)
#         count = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REWARDS'
#
#     Rewards.create_table()
#     return Rewards
#
#
# def getCompletedRewards():
#     class CompletedRewards(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         type = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'COMPLETEDREWARDS'
#
#     CompletedRewards.create_table()
#     return CompletedRewards
#
#
# def getNotifs():
#     class Notifs(Model):
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         tag = IntegerField(default=0)
#         every = IntegerField(default=0)
#         status = IntegerField(default=0)
#         time = BigIntegerField(default=0)
#         name = TextField(null=True)
#         description = TextField(null=True)
#         text = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'NOTIFICATIONS'
#
#     Notifs.create_table()
#     return Notifs
#
#
# def getTypeQueue():
#     class TypeQueue(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         uid = IntegerField(default=0)
#         type = TextField(null=True)
#         additional = TextField(null=True)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'TYPEQUEUE'
#
#     TypeQueue.create_table()
#     return TypeQueue
#
#
# def getReportWarns():
#     class ReportWarns(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         warns = IntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REPORTWARNS'
#
#     ReportWarns.create_table()
#     return ReportWarns
#
#
# def getMuted():
#     class Muted(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         uid = IntegerField(default=0, index=True, unique=True)
#         chat_id = IntegerField(default=0)
#         time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'MUTEDUSERS'
#
#     Muted.create_table()
#     return Muted
#
#
# def getReboots():
#     class Reboot(Model):
#         """
#         ORM model of the Chat table
#         """
#
#         chat_id = IntegerField(default=0, index=True, unique=True)
#         sended = BooleanField(default=0)
#         time = BigIntegerField(default=0)
#
#         class Meta:
#             primary_key = False
#             database = pdbhandle
#             db_table = f'REBOOTS'
#
#     Reboot.create_table()
#     return Reboot
#
#
# if __name__ == '__main__':
#     print(f'all tables: {dbhandle.get_tables().sort()}')
