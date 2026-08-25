import argparse
import os
import sys
from datetime import date
from pathlib import Path

from .config import (
    DOMAIN_ROOTS,
    ENABLED_SOURCES,
    EXCLUDE_ROOTS,
    KEEP_UNKNOWN_EXPERIENCE,
    MAX_EXPERIENCE_YEARS,
    ROLE_ROOTS,
)
from .experience import ExperienceFilter
from .http import build_session
from .matching import TitleFilter
from .notify import TelegramNotifier, render
from .sources import REGISTRY
from .telegraph import publish
from .state import State

DEFAULT_STATE = Path(__file__).resolve().parent.parent / "data" / "seen.json"


def collect(session, title_filter, experience_filter, sources):
    found, errors = [], []
    for name in sources:
        module = REGISTRY[name]
        try:
            by_title = [v for v in module.fetch(session) if title_filter.matches(v.title)]
        except Exception as exc:
            errors.append((name, f"{type(exc).__name__}: {exc}"))
            print(f"[!] {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        # Дубли схлопываются до фильтра по опыту, иначе счётчик отсева
        # считает копии одной вакансии (у Т-Банка их сотни).
        unique = {v.key: v for v in by_title}
        matched = {
            key: v
            for key, v in unique.items()
            if experience_filter.matches(v.title, v.experience)
        }
        dropped = len(unique) - len(matched)
        print(
            f"[+] {name}: подходящих вакансий {len(matched)}"
            + (f" (отсеяно по опыту {dropped})" if dropped else "")
        )
        found.extend(matched.values())
    return found, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Ежедневный обход карьерных сайтов")
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ничего не отправлять и не трогать файл состояния",
    )
    parser.add_argument("--source", action="append", dest="sources")
    args = parser.parse_args()

    sources = args.sources or list(ENABLED_SOURCES)
    unknown = [name for name in sources if name not in REGISTRY]
    if unknown:
        parser.error(f"неизвестные источники: {', '.join(unknown)}")

    title_filter = TitleFilter(ROLE_ROOTS, DOMAIN_ROOTS, EXCLUDE_ROOTS)
    experience_filter = ExperienceFilter(MAX_EXPERIENCE_YEARS, KEEP_UNKNOWN_EXPERIENCE)
    session = build_session()
    vacancies, errors = collect(session, title_filter, experience_filter, sources)
    vacancies.sort(key=lambda v: (v.company, v.title))

    state = State(args.state)
    first_run = not state.seeded
    fresh = state.split_new(vacancies)

    if args.dry_run:
        report_url = publish(vacancies, f"Вакансии аналитика — {date.today():%d.%m.%Y}")
        print(f"страница со списком: {report_url}")
        for vacancy in vacancies:
            mark = vacancy.experience or "опыт не указан"
            print(f"  {vacancy.company:16} {vacancy.title}  [{mark}]  {vacancy.url}")
        print(f"\nвсего {len(vacancies)}, из них новых {len(fresh)}")
        return 1 if errors and not vacancies else 0

    notifier = TelegramNotifier.from_env()
    report_url = publish(vacancies, f"Вакансии аналитика — {date.today():%d.%m.%Y}")
    if first_run:
        message = (
            f"<b>Мониторинг вакансий запущен</b>\n"
            f"В каталогах сейчас {len(vacancies)} подходящих вакансий. "
            f"Дальше будут приходить только новые."
        )
        if errors:
            message += "\n\nИсточники с ошибками: " + ", ".join(n for n, _ in errors)
        if notifier:
            notifier.send(message, report_url)
        print(f"Первый запуск: записано {len(vacancies)} вакансий без уведомления")
    elif fresh or errors:
        if notifier:
            notifier.send(render(fresh, errors), report_url)
        print(f"Отправлено новых вакансий: {len(fresh)}")
    else:
        print("Новых вакансий нет")

    if not notifier:
        print("[!] TELEGRAM_TOKEN/TELEGRAM_CHAT_ID не заданы — уведомление пропущено",
              file=sys.stderr)

    state.purge_expired()
    state.save()
    _write_summary(vacancies, fresh, errors, first_run)
    return 1 if errors and not vacancies else 0


def _write_summary(vacancies, fresh, errors, first_run):
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not path:
        return
    lines = [
        "## Мониторинг вакансий",
        "",
        f"- подходящих вакансий в каталогах: **{len(vacancies)}**",
        f"- новых с прошлого запуска: **{0 if first_run else len(fresh)}**",
    ]
    if errors:
        lines += ["", "### Источники с ошибками", ""]
        lines += [f"- `{name}` — {message}" for name, message in errors]
    if fresh and not first_run:
        lines += ["", "### Новые вакансии", ""]
        lines += [f"- {v.company} — [{v.title}]({v.url})" for v in fresh]
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
