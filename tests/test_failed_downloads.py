"""Failed Downloads page lists and clears dead URLs separately from release names."""

import unittest

from sickchill.oldbeard import db
from sickchill.views.manage.index import _clear_failed_downloads, _failed_download_rows
from tests import conftest


class FailedDownloadListTests(conftest.SickChillTestDBCase):
    def setUp(self):
        super().setUp()
        connection = db.DBConnection("failed.db")
        connection.action("DELETE FROM failed")
        if connection.has_table("dead_urls"):
            connection.action("DELETE FROM dead_urls")

    def test_dead_urls_are_listed_and_cleared_without_the_release_name(self):
        connection = db.DBConnection("failed.db")
        connection.action('INSERT INTO failed ("release", size, provider) VALUES (?, ?, ?)', ["Show_S01E01", 10, "Indexer"])
        connection.action(
            "INSERT INTO dead_urls (url, name, provider, date) VALUES (?, ?, ?, ?)",
            ["http://indexer/dead", "Show.S01E01", "Indexer", "20261119120000"],
        )

        failed_rows, dead_rows = _failed_download_rows(connection, "100")

        self.assertEqual([row["release"] for row in failed_rows], ["Show_S01E01"])
        self.assertEqual([(row["url"], row["name"]) for row in dead_rows], [("http://indexer/dead", "Show.S01E01")])

        _clear_failed_downloads(connection, [], ["http://indexer/dead"])
        failed_rows, dead_rows = _failed_download_rows(connection, "0")

        self.assertEqual([row["release"] for row in failed_rows], ["Show_S01E01"])
        self.assertEqual(dead_rows, [])

    def test_failed_downloads_page_renders_a_clearable_dead_url(self):
        from sickchill import settings
        from sickchill.views.common import get_lookup

        settings.THEME_NAME = "dark"
        settings.GUI_LANG = "en"
        settings.WEB_ROOT = ""
        settings.ANON_REDIRECT = ""
        settings.DATE_PRESET = "%Y-%m-%d"
        settings.TIME_PRESET = "%H:%M"
        page = get_lookup().get_template("manage_failedDownloads.mako")
        html = page.render(
            title="Failed Downloads",
            header="Failed Downloads",
            topmenu="manage",
            controller="manage",
            action="failedDownloads",
            submenu=[],
            limit="100",
            current_user=None,
            static_url=lambda path, include_version=True: path,
            manage_torrents_url="",
            page_load_start_time=0,
            mako_load_start_time=0,
            process_id="1",
            failedResults=[{"release": "Show_S01E01", "size": -1, "provider": "Indexer"}],
            deadUrls=[{"url": 'http://indexer/a&b"c', "name": "Show.S01E01", "provider": "Indexer", "date": "20261119120000"}],
        )

        self.assertIn("Show.S01E01", html)
        self.assertIn("Dead link", html)
        self.assertIn('data-dead-url="http://indexer/a&amp;b&#34;c"', html)
        self.assertIn('class="removeCheck"', html)
        self.assertIn("Show_S01E01", html)


if __name__ == "__main__":
    unittest.main()
