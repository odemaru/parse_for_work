"""Отбор вакансий по требуемому опыту.

Поле с опытом отдают не все: МТС, Wildberries, X5 и Северсталь пишут его
явно, а Т-Банк, Lamoda и Магнит — нет. Поэтому опыт оценивается с двух
сторон: по самому полю, когда оно есть, и по грейду в названии, который
есть всегда. «Стажёр» и «junior» проходят независимо от поля, «senior»,
«тимлид» и «руководитель» отсекаются независимо от него же.
"""

import re

from .matching import normalize

JUNIOR_MARKERS = ("stazher", "stager", "intern", "trainee", "junior", "dzhun")

SENIOR_MARKERS = (
    "senior", "lead", "lid", "head", "chief", "principal",
    "timlid", "rukovoditel", "starsh", "vedush", "glavn", "direktor", "director",
)

_ZERO_EXPERIENCE = ("без опыта", "нет опыта", "не требует", "без опыт")

_WORD_NUMBERS = {
    "года": 1, "год": 1, "одного": 1, "двух": 2, "трех": 3,
    "четырех": 4, "пяти": 5, "шести": 6,
}

_RANGE = re.compile(r"(\d+)\s*[-–—]\s*\d+")
_FROM_DIGIT = re.compile(r"от\s+(\d+)")
_BEFORE_UNIT = re.compile(r"(\d+)\s*\+?\s*[хx]?\s*(?:лет|год)")
_FROM_WORD = re.compile(r"от\s+([а-я]+)")
_ANY_DIGIT = re.compile(r"(\d+)")


def min_years(text: str):
    """Нижняя граница требуемого опыта в годах; None — если не указан.

    Строки приходят и структурированные («От 1 года до 3 лет»), и свободные
    («Опыт работы BI-аналитиком от 2 лет», «от двух лет»).
    """
    if not text:
        return None
    lowered = text.lower().replace("ё", "е")
    if any(marker in lowered for marker in _ZERO_EXPERIENCE):
        return 0
    for pattern in (_RANGE, _FROM_DIGIT, _BEFORE_UNIT):
        match = pattern.search(lowered)
        if match:
            return int(match.group(1))
    match = _FROM_WORD.search(lowered)
    if match and match.group(1) in _WORD_NUMBERS:
        return _WORD_NUMBERS[match.group(1)]
    match = _ANY_DIGIT.search(lowered)
    return int(match.group(1)) if match else None


def _has_marker(text: str, words: set, markers) -> bool:
    for marker in markers:
        # Короткие маркеры ищутся отдельным словом: "lid" иначе всплывает
        # внутри «консолидации», а "head" — внутри headhunter.
        if len(marker) <= 5:
            if marker in words:
                return True
        elif marker in text:
            return True
    return False


class ExperienceFilter:
    def __init__(self, max_years: int, keep_unknown: bool = True):
        self.max_years = max_years
        self.keep_unknown = keep_unknown

    def matches(self, title: str, experience: str = "") -> bool:
        normalized = normalize(title)
        words = set(normalized.split())
        if _has_marker(normalized, words, JUNIOR_MARKERS):
            return True
        if _has_marker(normalized, words, SENIOR_MARKERS):
            return False
        years = min_years(experience)
        if years is None:
            return self.keep_unknown
        return years <= self.max_years
