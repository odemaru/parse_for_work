import html
import json
import os
import sys
from pathlib import Path

import requests

from .config import DISABLED_SOURCES, REQUEST_TIMEOUT

API = "https://api.telegram.org/bot{token}/{method}"
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

    def send(self, text: str, button_url: str | None = None):
        """Недоступность одного получателя не отменяет доставку остальным."""
        failures = []
        for chat_id in self.chat_ids:
            try:
                self._send_to(chat_id, text, button_url)
            except requests.RequestException as exc:
                failures.append(f"{chat_id}: {exc}")
                print(f"[!] Telegram, чат {chat_id}: {exc}", file=sys.stderr)
        if failures and len(failures) == len(self.chat_ids):
            raise RuntimeError("не доставлено ни в один чат: " + "; ".join(failures))

    def send_animation(self, path, caption: str, button_url: str | None = None):
        """Шлёт гифку с подписью; если файла нет — обычное сообщение."""
        if not Path(path).is_file():
            print(f"[!] {path} не найден, вместо гифки уйдёт текст", file=sys.stderr)
            self.send(caption, button_url)
            return
        failures = []
        for chat_id in self.chat_ids:
            try:
                with open(path, "rb") as animation:
                    data = {
                        "chat_id": chat_id,
                        "caption": caption,
                        "parse_mode": "HTML",
                    }
                    if button_url:
                        data["reply_markup"] = _button(button_url)
                    response = requests.post(
                        API.format(token=self.token, method="sendAnimation"),
                        data=data,
                        files={"animation": animation},
                        timeout=REQUEST_TIMEOUT,
                    )
                    response.raise_for_status()
            except requests.RequestException as exc:
                failures.append(f"{chat_id}: {exc}")
                print(f"[!] Telegram, чат {chat_id}: {exc}", file=sys.stderr)
        if failures and len(failures) == len(self.chat_ids):
            raise RuntimeError("не доставлено ни в один чат: " + "; ".join(failures))

    def _send_to(self, chat_id: str, text: str, button_url: str | None = None):
        chunks = list(_split(text))
        for index, chunk in enumerate(chunks):
            payload = {
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            # Кнопка вешается только на последнее сообщение, иначе она
            # повторится под каждым куском длинного дайджеста.
            if button_url and index == len(chunks) - 1:
                payload["reply_markup"] = _button(button_url)
            response = requests.post(
                API.format(token=self.token, method="sendMessage"),
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()


def _button(url: str) -> str:
    return json.dumps(
        {"inline_keyboard": [[{"text": "📋 Показать все вакансии", "url": url}]]}
    )


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
            meta = " · ".join(
                filter(None, (vacancy.location, vacancy.experience, vacancy.published))
            )
            if meta:
                lines.append(f"  <i>{html.escape(meta)}</i>")
        lines.append("")
    if errors:
        lines.append("<b>Источники с ошибками</b>")
        for source, message in errors:
            lines.append(f"• {html.escape(source)}: {html.escape(message)}")
    return "\n".join(lines).strip()


def render_sources(counts, errors) -> str:
    """Сводка по источникам: откуда собираются вакансии и что там сейчас."""
    lines = ["<b>Откуда собираются вакансии</b>", ""]
    failed = dict(errors)
    for company in sorted(counts):
        if company in failed:
            lines.append(f"• {html.escape(company)} — <i>сейчас недоступен</i>")
        else:
            lines.append(f"• {html.escape(company)} — {counts[company]}")
    if DISABLED_SOURCES:
        lines += ["", "<b>Пока не подключены</b>"]
        for company, reason in DISABLED_SOURCES.items():
            lines.append(f"• {html.escape(company)} — {html.escape(reason)}")
    lines += [
        "",
        "<i>Ищутся продуктовые аналитики и аналитики данных "
        "с опытом до трёх лет включительно.</i>",
    ]
    return "\n".join(lines)


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
