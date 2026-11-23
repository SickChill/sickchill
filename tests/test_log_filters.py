import tempfile
import threading
import unittest
from pathlib import Path

from sickchill import logger
from sickchill.views.index import webserver_thread_name


def _filtered(lines, log_filter):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sickchill.log"
        path.write_text("".join(lines), encoding="utf-8")
        previous = logger.Wrapper.instance.log_file
        logger.Wrapper.instance.log_file = str(path)
        try:
            return logger.log_data(logger.INFO, log_filter, "", 50)
        finally:
            logger.Wrapper.instance.log_file = previous


class NotificationLogFilterTests(unittest.TestCase):
    def test_notifications_includes_every_suffix(self):
        lines = [
            "2026-11-20 13:25:27 INFO :: NOTIFICATIONS :: scheduler\n",
            "2026-11-20 13:25:27 INFO :: NOTIFICATIONS-DISCORD :: sent\n",
            "2026-11-20 13:25:27 INFO :: NOTIFICATIONS-EMAIL :: sent\n",
            "2026-11-20 13:25:27 INFO :: SHOWQUEUE-UPDATE :: other\n",
        ]
        data = _filtered(lines, "NOTIFICATIONS")

        self.assertEqual(len(data), 3)
        self.assertTrue(all("NOTIFICATIONS" in line for line in data))
        self.assertFalse(any("SHOWQUEUE" in line for line in data))


class LogFilterListTests(unittest.TestCase):
    LINES = (
        "2026-11-20 13:25:27 INFO :: WEBSERVER :: listening\n",
        "2026-11-20 13:25:27 INFO :: WEBSERVER-HOME :: displayShow\n",
        "2026-11-20 13:25:27 INFO :: WEBSERVER-HOMENEWS :: news\n",
        "2026-11-20 13:25:27 INFO :: WEBSERVER-MANAGESEARCHES :: searches\n",
        "2026-11-20 13:25:27 INFO :: SEARCHQUEUE-PROPER-SEARCH :: proper\n",
        "2026-11-20 13:25:27 INFO :: FINDPROPERS :: scheduler\n",
        "2026-11-20 13:25:27 INFO :: SEARCHQUEUE-SUBTITLE-12-1x2 :: subtitle\n",
        "2026-11-20 13:25:27 INFO :: FINDSUBTITLES :: scheduler\n",
    )

    def test_removed_filters_are_gone(self):
        for name in ("SEARCHQUEUE-RSS", "ERROR", "TORNADO", "Thread"):
            self.assertNotIn(name, logger.LOG_FILTERS)

    def test_webserver_includes_every_page(self):
        data = _filtered(self.LINES, "WEBSERVER")

        self.assertEqual(len(data), 4)
        self.assertTrue(all("WEBSERVER" in line for line in data))

    def test_webserver_home_includes_home_pages_only(self):
        data = _filtered(self.LINES, "WEBSERVER-HOME")

        self.assertEqual(len(data), 2)
        self.assertTrue(any("WEBSERVER-HOME ::" in line for line in data))
        self.assertTrue(any("WEBSERVER-HOMENEWS ::" in line for line in data))

    def test_proper_search_is_separate_from_the_scheduler(self):
        data = _filtered(self.LINES, "SEARCHQUEUE-PROPER-SEARCH")

        self.assertEqual(len(data), 1)
        self.assertIn("SEARCHQUEUE-PROPER-SEARCH", data[0])

    def test_subtitle_search_includes_episode_jobs(self):
        data = _filtered(self.LINES, "SEARCHQUEUE-SUBTITLE")

        self.assertEqual(len(data), 1)
        self.assertIn("SEARCHQUEUE-SUBTITLE-12-1x2", data[0])


class WebServerThreadNameTests(unittest.TestCase):
    def test_page_name_has_no_pool_index(self):
        class Home:
            pass

        self.assertEqual(webserver_thread_name(Home()), "WEBSERVER-HOME")

    def test_async_call_renames_the_worker(self):
        class Home:
            pass

        handler = Home()
        worker = threading.current_thread()
        previous = worker.name
        try:
            from sickchill.views.index import WebHandler

            WebHandler.async_call.__wrapped__(handler, lambda: worker.name, 0)
            self.assertEqual(worker.name, "WEBSERVER-HOME")
        finally:
            worker.name = previous
