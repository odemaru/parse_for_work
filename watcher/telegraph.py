"""Публикация полного списка вакансий отдельной страницей.

Telegraph — сервис самого Telegram: не требует ни аккаунта, ни секретов,
а ссылка на страницу разворачивается прямо в чате. Это позволяет держать
под уведомлением кнопку «Все вакансии», не поднимая сервер, который
слушал бы нажатия.
"""

import json
import sys

import requests

from .config import REQUEST_TIMEOUT
from .http import USER_AGENT

API = "https://api.telegra.ph"
MAX_LINE = 200


def publish(vacancies, title: str):
    """Возвращает адрес страницы или None, если Telegraph недоступен."""
    if not vacancies:
        return None
    try:
        account = _call(
            "createAccount",
            {"short_name": "jobwatch", "author_name": "Мониторинг вакансий"},
        )
        page = _call(
            "createPage",
            {
                "access_token": account["result"]["access_token"],
                "title": title[:256],
                "content": json.dumps(_content(vacancies), ensure_ascii=False),
                "return_content": "false",
            },
        )
        return page["result"]["url"]
    except (requests.RequestException, KeyError, ValueError, RuntimeError) as exc:
        print(f"[!] Telegraph недоступен, кнопки не будет: {exc}", file=sys.stderr)
        return None


def _call(method: str, params: dict) -> dict:
    # Только POST: содержимое страницы не помещается в строку запроса,
    # и на длинном списке вакансий GET упирается в 400 от nginx.
    response = requests.post(
        f"{API}/{method}",
        data=params,
        timeout=REQUEST_TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        payload = response.json()
    except ValueError:
        raise RuntimeError(
            f"{method}: HTTP {response.status_code}, ответ не JSON: "
            f"{response.text[:200]!r}"
        ) from None
    if not payload.get("ok"):
        raise RuntimeError(f"{method}: {payload.get('error', 'неизвестная ошибка')}")
    return payload


def _content(vacancies):
    nodes = []
    by_company: dict[str, list] = {}
    for vacancy in vacancies:
        by_company.setdefault(vacancy.company, []).append(vacancy)
    for company in sorted(by_company):
        items = by_company[company]
        nodes.append({"tag": "h4", "children": [f"{company} — {len(items)}"]})
        for vacancy in items:
            line = [
                {
                    "tag": "a",
                    "attrs": {"href": vacancy.url},
                    "children": [vacancy.title[:MAX_LINE]],
                }
            ]
            meta = " · ".join(
                filter(None, (vacancy.location, vacancy.experience, vacancy.published))
            )
            if meta:
                line.append(f" — {meta}")
            nodes.append({"tag": "p", "children": line})
    return nodes
