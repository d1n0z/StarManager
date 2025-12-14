from dataclasses import dataclass
from functools import total_ordering

from StarManager.core.managers.access_level import CachedAccessLevelRow


@total_ordering
@dataclass(frozen=True)
class SimpleAccessLevel:
    access_level: int
    is_custom: bool

    @classmethod
    def from_cached(cls, row: CachedAccessLevelRow) -> "SimpleAccessLevel":
        return cls(
            access_level=row.access_level, is_custom=row.custom_level_name is not None
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SimpleAccessLevel):
            return (
                self.is_custom == other.is_custom
                and self.access_level == other.access_level
            )
        try:
            return self.access_level == other
        except Exception:
            return NotImplemented

    def __lt__(self, other: object) -> bool:
        if isinstance(other, SimpleAccessLevel):
            if self.is_custom != other.is_custom:
                return self.is_custom and not other.is_custom
            return self.access_level < other.access_level
        try:
            return self.access_level < other  # type: ignore
        except Exception:
            return NotImplemented
