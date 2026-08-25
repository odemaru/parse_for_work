import json
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import STATE_TTL_DAYS


class State:
    """Помнит, о каких вакансиях уже уведомляли.

    Дата обновляется при каждой встрече вакансии, а не только при первой,
    иначе долгоживущая вакансия выпала бы по TTL и пришла повторно.
    """

    def __init__(self, path: Path):
        self.path = path
        self.seen: dict[str, str] = {}
        self.seeded = False
        if path.exists():
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.seen = payload.get("seen", {})
            self.seeded = payload.get("seeded", False)

    def split_new(self, vacancies):
        fresh = [v for v in vacancies if v.key not in self.seen]
        today = date.today().isoformat()
        for vacancy in vacancies:
            self.seen[vacancy.key] = today
        return fresh

    def purge_expired(self):
        cutoff = date.today() - timedelta(days=STATE_TTL_DAYS)
        self.seen = {
            key: seen_at
            for key, seen_at in self.seen.items()
            if _parse(seen_at) >= cutoff
        }

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "seeded": True,
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "seen": dict(sorted(self.seen.items())),
        }
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def _parse(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        return date.today()
