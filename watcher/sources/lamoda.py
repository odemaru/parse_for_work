import re

from ..models import Vacancy
from ._sitemap import iter_urls, title_from_slug

NAME = "lamoda"
COMPANY = "Lamoda"
SITEMAP = "https://job.lamoda.ru/sitemap.xml"

_VACANCY_URL = re.compile(
    r"/vacancies/(?P<city>[^/]+)/(?P<slug>.+?)--(?P<uid>\d+)$"
)


def fetch(session):
    for url, lastmod in iter_urls(session, SITEMAP):
        match = _VACANCY_URL.search(url)
        if not match:
            continue
        yield Vacancy(
            source=NAME,
            company=COMPANY,
            external_id=match.group("uid"),
            title=title_from_slug(match.group("slug")),
            url=url,
            location=title_from_slug(match.group("city")),
            published=lastmod,
        )
