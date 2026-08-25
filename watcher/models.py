from dataclasses import dataclass


@dataclass(frozen=True)
class Vacancy:
    source: str
    company: str
    external_id: str
    title: str
    url: str
    location: str = ""
    published: str = ""
    experience: str = ""

    @property
    def key(self) -> str:
        return f"{self.source}:{self.external_id}"
