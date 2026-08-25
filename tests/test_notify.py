import unittest

from watcher.models import Vacancy
from watcher.notify import parse_chat_ids, render, render_sources


class ParseChatIdsTest(unittest.TestCase):
    def test_single_and_multiple(self):
        self.assertEqual(parse_chat_ids("111222333"), ["111222333"])
        self.assertEqual(parse_chat_ids("111,222"), ["111", "222"])

    def test_tolerates_spaces_and_empties(self):
        self.assertEqual(parse_chat_ids(" 111 , ,222, "), ["111", "222"])
        self.assertEqual(parse_chat_ids(""), [])


class RenderTest(unittest.TestCase):
    def test_escapes_html_in_titles(self):
        vacancy = Vacancy("mts", "МТС", "1", "Аналитик <b>данных</b>", "https://x/", "Москва")
        message = render([vacancy], [])
        self.assertIn("&lt;b&gt;", message)
        self.assertIn('<a href="https://x/">', message)

    def test_reports_failed_sources(self):
        message = render([], [("magnit", "HTTPError: 502")])
        self.assertIn("Источники с ошибками", message)
        self.assertIn("magnit", message)


class RenderSourcesTest(unittest.TestCase):
    def test_lists_every_source_including_empty(self):
        message = render_sources({"МТС": 11, "Северсталь": 0}, [])
        self.assertIn("МТС — 11", message)
        self.assertIn("Северсталь — 0", message)

    def test_marks_failed_source_instead_of_zero(self):
        message = render_sources({"Магнит": 0}, [("Магнит", "HTTPError: 502")])
        self.assertIn("сейчас недоступен", message)
        self.assertNotIn("Магнит — 0", message)

    def test_mentions_disabled_companies(self):
        message = render_sources({"МТС": 1}, [])
        self.assertIn("Ozon", message)
        self.assertIn("Альфа-Банк", message)


if __name__ == "__main__":
    unittest.main()
