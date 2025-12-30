from typing import Optional

from ..base import BaseManagerGroup
from .chat_filters import ChatFiltersManager
from .filters_exceptions import FiltersExceptionsManager
from .global_filters import GlobalFiltersManager


class FiltersManager(BaseManagerGroup):
    def __init__(self):
        self.chat_f = ChatFiltersManager()
        self.global_f = GlobalFiltersManager()
        self.exceptions_f = FiltersExceptionsManager()
        self.managers = [self.chat_f, self.global_f, self.exceptions_f]

    async def matches(self, chat_id: Optional[int], owner_id: Optional[int], text: str):
        matched = None
        if chat_id:
            matched = self.chat_f.matches(chat_id, text)
            if matched:
                return matched

        if matched is None and owner_id:
            matched = self.global_f.matches(owner_id, text)
            if (
                matched
                and chat_id
                and await self.exceptions_f.filter_exists(chat_id, matched)
            ):
                return None

        return matched


__ALL__ = [FiltersManager]
