import html
import os
import sys

import requests

from .config import REQUEST_TIMEOUT

API = "https://api.telegram.org/bot{token}/sendMessage"
MAX_MESSAGE = 3800


class TelegramNotifier:
    def __init__(self, token: str, chat_ids):
        self.token = token
        self.chat_ids = list(chat_ids)

    @classmethod
    def from_env(cls):
        token = os.environ.get("TELEGRAM_TOKEN", "").strip()
        chat_ids = parse_chat_ids(os.environ.get("TELEGRAM_CHAT_ID", ""))
        if not token or not chat_ids:
            return None
        return cls(token, chat_ids)

    def send(self, text: str):
        """Недоступность одного получателя не отменяет доставку остальным."""
        failures = []
        for chat_id in self.chat_ids:
            try:
                self._send_to(chat_id, text)
            except requests.RequestException as exc:
                failures.append(f"{chat_id}: {exc}")
                print(f"[!] Telegram, чат {chat_id}: {exc}", file=sys.stderr)
        if failures and len(failures) == len(self.chat_ids):
            raise RuntimeError("не доставлено ни в один чат: " + "; ".join(failures))

    def _send_to(self, chat_id: str, text: str):
        for chunk in _split(text):
            response = requests.post(
                API.format(token=self.token),
                json={
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()


def parse_chat_ids(raw: str):
    """TELEGRAM_CHAT_ID хранит один id или несколько через запятую."""
    return [part.strip() for part in raw.split(",") if part.strip()]


def render(vacancies, errors) -> str:
    lines = [f"<b>Новых вакансий: {len(vacancies)}</b>", ""]
    by_company: dict[str, list] = {}
    for vacancy in vacancies:
        by_company.setdefault(vacancy.company, []).append(vacancy)
    for company in sorted(by_company):
        lines.append(f"<b>{html.escape(company)}</b>")
        for vacancy in by_company[company]:
            title = html.escape(vacancy.title)
            lines.append(f'• <a href="{html.escape(vacancy.url)}">{title}</a>')
            meta = " · ".join(filter(None, (vacancy.location, vacancy.published)))
            if meta:
                lines.append(f"  <i>{html.escape(meta)}</i>")
        lines.append("")
    if errors:
        lines.append("<b>Источники с ошибками</b>")
        for source, message in errors:
            lines.append(f"• {html.escape(source)}: {html.escape(message)}")
    return "\n".join(lines).strip()


def _split(text: str):
    chunk: list[str] = []
    size = 0
    for line in text.split("\n"):
        if size + len(line) + 1 > MAX_MESSAGE and chunk:
            yield "\n".join(chunk)
            chunk, size = [], 0
        chunk.append(line)
        size += len(line) + 1
    if chunk:
        yield "\n".join(chunk)
