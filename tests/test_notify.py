import unittest

from watcher.models import Vacancy
from watcher.notify import parse_chat_ids, render


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


if __name__ == "__main__":
    unittest.main()
