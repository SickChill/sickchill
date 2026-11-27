import logging
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


def _format_censored(msg: str) -> str:
    record = logging.LogRecord("sickchill", logging.DEBUG, __file__, 1, msg, (), None)
    return logger.DispatchFormatter("{message}").format(record)


class LogCensorTests(unittest.TestCase):
    def setUp(self):
        self._saved = dict(logger.censored_items)
        logger.censored_items.clear()

    def tearDown(self):
        logger.censored_items.clear()
        logger.censored_items.update(self._saved)

    def test_register_skips_none_and_placeholders(self):
        logger.register_censored(("t", "none"), None)
        logger.register_censored(("t", "none_str"), "None")
        logger.register_censored(("t", "zero"), "0")
        logger.register_censored(("t", "short"), "ab")
        logger.register_censored(("t", "empty"), "")
        self.assertEqual(logger.censored_items, {})

    def test_none_placeholder_is_not_hashed_in_quality_or_client_logs(self):
        logger.register_censored(("t", "none"), "None")
        quality_line = "Any,Best = [ 720p HDTV, 1080p HDTV ] [ None ] Found = [ 1080p WEB-DL ]"
        formatted = _format_censored(quality_line)
        self.assertIn("None", formatted)
        self.assertNotIn(logger.CENSOR_PLACEHOLDER, formatted)

        client_line = "Posting as file with {'ratio_limit': None, 'seeding_time_limit': None, 'tags': 'sickchill'}"
        formatted = _format_censored(client_line)
        self.assertIn("None", formatted)
        self.assertNotIn(logger.CENSOR_PLACEHOLDER, formatted)

        pp_line = "Processing /tmp/show.mkv (None)"
        formatted = _format_censored(pp_line)
        self.assertIn("(None)", formatted)

    def test_password_and_username_are_hashed(self):
        logger.register_censored(("PROVIDERS", "torrentday.username"), "stephenbkk28")
        logger.register_censored(("PROVIDERS", "torrentday.password"), "TowerDestroyer28")
        formatted = _format_censored("With post data: username=stephenbkk28&password=TowerDestroyer28&submit.x=0&submit.y=0")
        self.assertNotIn("stephenbkk28", formatted)
        self.assertNotIn("TowerDestroyer28", formatted)
        self.assertIn("username=" + logger.CENSOR_PLACEHOLDER, formatted)
        self.assertIn("password=" + logger.CENSOR_PLACEHOLDER, formatted)
        self.assertIn("submit.x=0", formatted)

    def test_redact_post_body_masks_form_and_json(self):
        form = logger.redact_post_body("username=stephenbkk28&password=TowerDestroyer28&submit.x=0&submit.y=0")
        self.assertIn("username=" + logger.CENSOR_PLACEHOLDER, form)
        self.assertIn("password=" + logger.CENSOR_PLACEHOLDER, form)
        self.assertIn("submit.x=0", form)

        payload = logger.redact_post_body('{"method": "auth.login", "params": [], "password": "secret-pass"}')
        self.assertNotIn("secret-pass", payload)
        self.assertIn(logger.CENSOR_PLACEHOLDER, payload)
        self.assertIn("auth.login", payload)

    def test_register_replaces_previous_value(self):
        logger.register_censored(("t", "password"), "old-secret-value")
        logger.register_censored(("t", "password"), "new-secret-value")
        formatted = _format_censored("old-secret-value new-secret-value")
        self.assertIn("old-secret-value", formatted)
        self.assertNotIn("new-secret-value", formatted)
