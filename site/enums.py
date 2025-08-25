from enum import Enum


class LeaderboardType(str, Enum):
    COINS = "topcoins"
    MESSAGES = "topmessages"
    DUELS = "topduels"
    LEAGUES = "topleagues"
    REP = "toprep"
    MATH = "topmath"
    BONUS = "topbonus"

    def get_queries(self) -> tuple[str, str]:
        if self == LeaderboardType.COINS:
            base = "SELECT uid, coins AS value FROM xp ORDER BY coins DESC"
        elif self == LeaderboardType.MESSAGES:
            base = "SELECT uid, SUM(messages) AS value FROM messages GROUP BY uid ORDER BY value DESC"
        elif self == LeaderboardType.DUELS:
            base = "SELECT uid, wins AS value FROM duelwins ORDER BY wins DESC"
        elif self == LeaderboardType.LEAGUES:
            base = "SELECT uid, league, lvl FROM xp ORDER BY league DESC, lvl DESC"
        elif self == LeaderboardType.REP:
            base = "SELECT uid, rep AS value FROM reputation ORDER BY rep DESC"
        elif self == LeaderboardType.MATH:
            base = "SELECT winner AS uid, COUNT(*) AS value FROM mathgiveaway WHERE winner IS NOT NULL GROUP BY winner ORDER BY value DESC"
        elif self == LeaderboardType.BONUS:
            base = "SELECT uid, streak AS value FROM bonus ORDER BY streak DESC"
        else:
            raise ValueError("Unsupported leaderboard category")

        paginated = f"{base} OFFSET $1 LIMIT $2"
        return base, paginated
