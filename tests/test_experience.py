import unittest

from watcher.config import KEEP_UNKNOWN_EXPERIENCE, MAX_EXPERIENCE_YEARS
from watcher.experience import ExperienceFilter, min_years


class MinYearsTest(unittest.TestCase):
    def test_structured_fields(self):
        cases = {
            "Без опыта": 0,
            "Нет опыта": 0,
            "От 1 года до 3 лет": 1,
            "1-3 года": 1,
            "3-6 лет": 3,
            "От 3 до 6 лет": 3,
            "Более 6 лет": 6,
            "От 1 года": 1,
            "От 5 лет": 5,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(min_years(text), expected)

    def test_free_text_from_x5(self):
        """X5 пишет опыт прозой, без единого формата."""
        cases = {
            "от двух лет": 2,
            "от 3х лет": 3,
            "Опыт работы BI-аналитиком от 2 лет": 2,
            "Опыт работы не менее 1 года на аналогичной должности": 1,
            "От года в розничной торговле продуктами питания": 1,
            "1-3": 1,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(min_years(text), expected)

    def test_missing_is_unknown(self):
        self.assertIsNone(min_years(""))
        self.assertIsNone(min_years("Полная занятость"))


class ExperienceFilterTest(unittest.TestCase):
    def setUp(self):
        self.filter = ExperienceFilter(MAX_EXPERIENCE_YEARS, KEEP_UNKNOWN_EXPERIENCE)

    def test_keeps_junior_and_internships(self):
        for title in (
            "Стажер Дата аналитик Smart Rollout",
            "Стажёр-аналитик данных",
            "Junior product analyst",
            "Junior Data Analyst",
        ):
            with self.subTest(title=title):
                self.assertTrue(self.filter.matches(title, "От 5 лет"))

    def test_keeps_up_to_three_years(self):
        self.assertTrue(self.filter.matches("Продуктовый аналитик", "Без опыта"))
        self.assertTrue(self.filter.matches("Продуктовый аналитик", "От 1 года до 3 лет"))
        self.assertTrue(self.filter.matches("Аналитик данных", "1-3 года"))

    def test_drops_demanding_vacancies(self):
        self.assertFalse(self.filter.matches("Продуктовый аналитик", "От 5 лет"))
        self.assertFalse(self.filter.matches("Аналитик данных", "Более 6 лет"))

    def test_drops_senior_grades_by_title(self):
        """Т-Банк и Lamoda опыт не публикуют — грейд виден только в названии."""
        for title in (
            "Timlid produktovoj analitiki",
            "Rukovoditel produktovoj analitiki collection b2b",
            "Head of product analytics at auto loans",
            "Lid produktovoy analitiki",
            "Starshiy produktoviy analitik delivery",
            "Ведущий продуктовый аналитик",
            "Middle+/Senior Data Analyst",
        ):
            with self.subTest(title=title):
                self.assertFalse(self.filter.matches(title, ""))

    def test_short_markers_do_not_match_inside_words(self):
        """"lid" не должен срабатывать внутри «консолидации»."""
        self.assertTrue(self.filter.matches("Аналитик данных консолидации", ""))

    def test_unknown_experience_is_kept(self):
        self.assertTrue(self.filter.matches("Produktovyj analitik", ""))


if __name__ == "__main__":
    unittest.main()
