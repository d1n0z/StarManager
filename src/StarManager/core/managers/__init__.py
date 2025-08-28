from StarManager.core.managers.antispam_messages import AntispamMessagesManager
from StarManager.core.managers.commands_cooldown import CommandsCooldownManager
from StarManager.core.managers.duel import DuelLockManager
from StarManager.core.managers.raid import RaidManager

antispam = AntispamMessagesManager()
commands_cooldown = CommandsCooldownManager()
duel_lock = DuelLockManager()
raid = RaidManager()
