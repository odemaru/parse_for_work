import re

from ..config import REQUEST_TIMEOUT
from ..http import USER_AGENT

_URL_BLOCK = re.compile(
    r"<loc>(?P<loc>[^<]+)</loc>(?:\s*<lastmod>(?P<lastmod>[^<]+)</lastmod>)?",
    re.IGNORECASE,
)


def iter_urls(session, sitemap_url):
    """Читает sitemap потоком — у Т-Банка он весит больше 10 МБ."""
    with session.get(
        sitemap_url,
        timeout=REQUEST_TIMEOUT,
        stream=True,
        headers={"User-Agent": USER_AGENT},
    ) as response:
        response.raise_for_status()
        response.encoding = response.encoding or "utf-8"
        buffer = ""
        for chunk in response.iter_content(chunk_size=1 << 16, decode_unicode=True):
            if not chunk:
                continue
            buffer += chunk
            last_end = 0
            for match in _URL_BLOCK.finditer(buffer):
                yield match.group("loc"), (match.group("lastmod") or "")[:10]
                last_end = match.end()
            buffer = buffer[last_end:] if last_end else buffer[-4096:]


def title_from_slug(slug: str) -> str:
    return slug.replace("_", " ").replace("-", " ").strip().capitalize()
