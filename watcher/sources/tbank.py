import re

from ..matching import normalize
from ..models import Vacancy
from ._sitemap import iter_urls, title_from_slug

NAME = "tbank"
COMPANY = "Т-Банк"

# Карточки вакансий рендерятся на сервере и не имеют публичного API,
# зато карьерный раздел выкладывает полный sitemap.
SITEMAPS = (
    "https://www.tbank.ru/storage/career/sitemaps/it_0.xml",
    "https://www.tbank.ru/storage/career/sitemaps/it_1.xml",
    "https://www.tbank.ru/storage/career/sitemaps/back_office_0.xml",
    "https://www.tbank.ru/storage/career/sitemaps/back_office_1.xml",
)

_VACANCY_URL = re.compile(
    r"/career/[^/]+/vacancy/[0-9a-f-]+/(?P<slug>[^/]+)/(?P<uid>[0-9a-f-]{36})/"
)


def fetch(session):
    for sitemap in SITEMAPS:
        for url, lastmod in iter_urls(session, sitemap):
            match = _VACANCY_URL.search(url)
            if not match:
                continue
            slug = match.group("slug")
            # Одна и та же роль лежит в sitemap десятками копий с разными uuid
            # (по одной на город и на команду), причём транслит гуляет между
            # копиями. Ключом берётся нормализованный slug, иначе
            # в уведомление приходит десяток одинаковых строк.
            yield Vacancy(
                source=NAME,
                company=COMPANY,
                external_id=normalize(slug).replace(" ", "-"),
                title=title_from_slug(slug),
                url=url,
                published=lastmod,
            )
