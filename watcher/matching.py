"""Отбор вакансий по названию.

Карьерные сайты отдают названия по-разному: у МТС и Магнита это русский текст,
у Т-Банка и Lamoda — только транслитерированный slug из URL, причём схемы
транслитерации у них не совпадают ("продуктовый" -> produktovyj у Т-Банка,
produktoviy у Lamoda). Поэтому всё приводится к латинице и схемы сводятся
к общему виду, после чего ищутся корни слов, а не целые фразы.
"""

import re

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "j", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

_SCHEME_QUIRKS = [
    (re.compile(r"kh"), "h"),
    (re.compile(r"shh|sch"), "sh"),
    (re.compile(r"ts"), "c"),
    (re.compile(r"yj|ij|iy|yi|yy"), "y"),
    (re.compile(r"oj|oy"), "o"),  # produktovoj / produktovoy — одно и то же
]


def normalize(text: str) -> str:
    lowered = (text or "").lower()
    latin = "".join(_CYRILLIC.get(ch, ch) for ch in lowered)
    for pattern, replacement in _SCHEME_QUIRKS:
        latin = pattern.sub(replacement, latin)
    return re.sub(r"[^a-z0-9]+", " ", latin).strip()


class TitleFilter:
    def __init__(self, role_roots, domain_roots, exclude_roots):
        self.role_roots = tuple(role_roots)
        self.domain_roots = tuple(domain_roots)
        self.exclude_roots = tuple(exclude_roots)

    def matches(self, title: str) -> bool:
        text = normalize(title)
        if not any(root in text for root in self.role_roots):
            return False
        if not any(root in text for root in self.domain_roots):
            return False
        return not any(root in text for root in self.exclude_roots)
