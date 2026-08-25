from ..http import get_json
from ..models import Vacancy

NAME = "mts"
COMPANY = "МТС"
API = "https://job.mts.ru/api/v2/catalog/v1/vacancies"
PAGE_SIZE = 100

# Фильтр по категории API не поддерживает, поэтому каталог выкачивается целиком
# и отсеивается уже на нашей стороне. Это ~30 запросов раз в сутки.
MAX_PAGES = 60


def fetch(session):
    offset = 0
    for _ in range(MAX_PAGES):
        payload = get_json(session, API, {"limit": PAGE_SIZE, "offset": offset})
        items = payload.get("data") or []
        if not items:
            return
        for item in items:
            cities = ", ".join(city["title"] for city in item.get("cities") or [])
            yield Vacancy(
                source=NAME,
                company=COMPANY,
                external_id=str(item["id"]),
                title=item.get("displayTitle") or item["title"],
                url=item.get("externalUrl") or f"https://job.mts.ru/jobs/{item['slug']}",
                location=cities,
                published=(item.get("publishedAt") or "")[:10],
                experience=(item.get("experience") or {}).get("title") or "",
            )
        pagination = (payload.get("meta") or {}).get("pagination") or {}
        offset += PAGE_SIZE
        if offset >= pagination.get("total", 0):
            return
