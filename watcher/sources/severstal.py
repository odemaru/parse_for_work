from bs4 import BeautifulSoup

from ..http import get_text
from ..models import Vacancy

NAME = "severstal"
COMPANY = "Северсталь"
LISTING = "https://career.severstal.com/vacancies/"

# Листинг накапливает результаты: ?page=N отдаёт первые N страниц сразу,
# поэтому весь каталог (~370 вакансий) забирается одним запросом.
PAGE_DEPTH = 60


def fetch(session):
    html = get_text(session, LISTING, {"page": PAGE_DEPTH})
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("a.card-vacancy"):
        href = card.get("href") or ""
        title = card.select_one(".card-vacancy__title-text")
        if not href or not title:
            continue
        place = card.select_one(".card-vacancy__place")
        published = card.select_one("time.card-vacancy__date")
        yield Vacancy(
            source=NAME,
            company=COMPANY,
            external_id=href.strip("/").split("/")[-1],
            title=title.get_text(strip=True),
            url=f"https://career.severstal.com{href}",
            location=place.get_text(strip=True) if place else "",
            published=published.get("datetime", "") if published else "",
        )
