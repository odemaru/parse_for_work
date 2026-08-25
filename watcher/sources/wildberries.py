from ..http import get_json
from ..models import Vacancy

NAME = "wildberries"
COMPANY = "Wildberries"
API = "https://career.rwb.ru/crm-api/api/v1/pub/vacancies"
PAGE_SIZE = 100


def fetch(session):
    offset = 0
    while True:
        payload = get_json(session, API, {"limit": PAGE_SIZE, "offset": offset})
        block = payload["data"]
        for item in block["items"]:
            yield Vacancy(
                source=NAME,
                company=COMPANY,
                external_id=str(item["id"]),
                title=item["name"],
                url=f"https://career.rwb.ru/vacancies/{item['id']}",
                location=item.get("city_title") or "",
            )
        offset += PAGE_SIZE
        if offset >= block["range"]["count"]:
            return
