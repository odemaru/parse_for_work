from ..config import MAGNIT_DIRECTIONS, MAGNIT_LOCALITIES
from ..http import get_json
from ..models import Vacancy

NAME = "magnit"
COMPANY = "Магнит"
API = "https://rabota.magnit.ru/api/v1/vacancy"
MAX_PAGES = 30


def fetch(session):
    for city, locality_id in MAGNIT_LOCALITIES.items():
        for direction in MAGNIT_DIRECTIONS:
            yield from _fetch_direction(session, city, locality_id, direction)


def _fetch_direction(session, city, locality_id, direction):
    page = 1
    while page <= MAX_PAGES:
        payload = get_json(
            session,
            API,
            {
                "locality_id[]": locality_id,
                "business_direction_id[]": direction,
                "overview": "list",
                "page": page,
            },
        )
        for item in payload.get("results") or []:
            yield Vacancy(
                source=NAME,
                company=COMPANY,
                external_id=str(item["id"]),
                title=item["name"],
                url=f"https://rabota.magnit.ru/vacancy/{item['id']}",
                location=city,
            )
        meta = payload.get("meta") or {}
        if not meta.get("has_more_pages"):
            return
        page += 1
