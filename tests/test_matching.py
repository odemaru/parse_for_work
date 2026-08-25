import unittest

from watcher.config import DOMAIN_ROOTS, EXCLUDE_ROOTS, ROLE_ROOTS
from watcher.matching import TitleFilter, normalize

MATCHING = [
    "Продуктовый аналитик",
    "produktovyj-analitik",
    "Starshiy produktoviy analitik delivery",
    "Timlid produktovoj analitiki",
    "Продуктовая аналитика",
    "Ведущий аналитик продукта",
    "Аналитик данных",
    "Data analyst (Департамент клиентского сервиса и опыта)",
    "Аналитик данных в HR-аналитику",
    "Middle Дата аналитик в МТС Гид [Big Data]",
    "Junior product analyst",
    "Full Stack Analytics / Product Analyst (AI-first)",
]

NOT_MATCHING = [
    "Системный аналитик",
    "Junior System Analyst DWH в РТК Data",
    "Biznes analitik",
    "Finansoviy analitik",
    "Hr analitik",
    "Marketingoviy analitik gp kh",
    "Маркетинговый аналитик (конвергентные продукты)",
    "Менеджер продукта (Видеоаналитика)",
    "Analitik operatsionnoy effektivnosti",
    "Аналитик SOC",
    "Аналитик 1С",
    "Аналитик продуктового качества",
    "Продавец-консультант",
    "Менеджер по продукту",
]


class NormalizeTest(unittest.TestCase):
    def test_transliteration_schemes_converge(self):
        """Т-Банк пишет produktovyj, Lamoda — produktoviy, сайт МТС — кириллицей."""
        expected = "produktovy analitik"
        for variant in ("Продуктовый аналитик", "produktovyj-analitik", "Produktoviy analitik"):
            self.assertEqual(normalize(variant), expected, variant)


class TitleFilterTest(unittest.TestCase):
    def setUp(self):
        self.title_filter = TitleFilter(ROLE_ROOTS, DOMAIN_ROOTS, EXCLUDE_ROOTS)

    def test_accepts_target_roles(self):
        for title in MATCHING:
            with self.subTest(title=title):
                self.assertTrue(self.title_filter.matches(title))

    def test_rejects_neighbouring_roles(self):
        for title in NOT_MATCHING:
            with self.subTest(title=title):
                self.assertFalse(self.title_filter.matches(title))


if __name__ == "__main__":
    unittest.main()
