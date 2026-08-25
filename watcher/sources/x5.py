from ..http import get_json
from ..models import Vacancy

NAME = "x5"
COMPANY = "X5 / Пятёрочка"
API = "https://rabota.x5.ru/api/v2/public/vacancies/"
PAGE_SIZE = 100

# У X5 есть серверный полнотекстовый поиск, поэтому весь каталог не нужен.
QUERIES = ("аналитик", "analyst")


def fetch(session):
    for query in QUERIES:
        page = 1
        while True:
            payload = get_json(
                session, API, {"search": query, "page": page, "page_size": PAGE_SIZE}
            )
            for item in payload.get("items", []):
                yield Vacancy(
                    source=NAME,
                    company=COMPANY,
                    external_id=str(item["id"]),
                    title=item["name"],
                    url=f"https://rabota.x5.ru/vacancies/{item['id']}",
                    location=item.get("city") or "",
                )
            next_page = payload.get("next_page")
            if not next_page:
                break
            page = next_page
