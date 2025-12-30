import re
import unicodedata
from dataclasses import dataclass
from typing import Optional, Set

import ahocorasick

_leet_map = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
        "!": "i",
        "|": "i",
        "+": "t",
    }
)

_zero_width_re = re.compile("[" + "\u200b\u200c\u200d\ufeff" + "]")
_re_duplicate = re.compile(r"(.)\1{2,}")


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s).lower()
    s = _zero_width_re.sub("", s)
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
    s = s.translate(_leet_map)
    s = "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )
    s = re.sub(r"[^0-9a-zа-яё]+", " ", s)
    s = _re_duplicate.sub(r"\1\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class Matcher:
    automaton: Optional[ahocorasick.Automaton] = None
    regex_list: Optional[list] = None
    normalized_filters: Optional[Set[str]] = None


def matches(matcher: Optional[Matcher], text: str) -> Optional[str]:
    if matcher is None:
        return None
    norm_msg = normalize_text(text)
    if not norm_msg:
        return None
    if matcher.normalized_filters and norm_msg in matcher.normalized_filters:
        return norm_msg
    if matcher.automaton is not None:
        for _, found in matcher.automaton.iter(norm_msg):
            return found
        return None
    for rx in matcher.regex_list or []:
        if res := rx.search(norm_msg):
            if res:
                return res.groups()[0]
    return None
