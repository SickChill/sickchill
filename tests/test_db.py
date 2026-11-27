"""
Test show database functionality.

Tests:
    DBBasicTests
    DBMultiTests
"""

import threading
import time
import unittest
from datetime import datetime

import sickchill
from tests import conftest


class DBBasicTests(conftest.SickChillTestDBCase):
    """
    Perform basic database tests.

    Tests:
        test_select
    """

    def setUp(self):
        """
        Set up base.
        """
        super().setUp()
        self.sc_db = sickchill.db.DBConnection()

    def test_select(self):
        """
        Test selecting from the database
        """
        self.sc_db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])


class DBMultiTests(conftest.SickChillTestDBCase):
    """
    Perform multi-threaded test of the database

    Tests:
        test_threaded
    """

    def setUp(self):
        """
        Set up base.
        """
        super().setUp()
        self.sc_db = sickchill.db.DBConnection()

    def select(self):
        """
        Select from the database.
        """
        self.sc_db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])

    def test_threaded(self):
        """
        Test multi-threaded selection from the database
        """
        for _ in range(4):
            thread = threading.Thread(target=self.select)
            thread.start()


class CacheDBTests(conftest.SickChillTestDBCase):
    def setUp(self):
        super().setUp()
        self.cache_db_con = sickchill.db.DBConnection("cache.db")
        sickchill.db.upgrade_database(self.cache_db_con, sickchill.databases.cache.InitialSchema)
        from sickchill.helper.network_timezones import sc_timezone

        cur_timestamp = int(time.mktime(datetime.now(tz=sc_timezone).timetuple()))
        self.record = (
            {
                "provider": "provider",
                "name": "name",
                "season": 1,
                "episodes": "|1|",
                "indexerid": 1,
                "url": "url",
                "time": cur_timestamp,
                "quality": "1",
                "release_group": "SICKCHILL",
                "version": 1,
                "seeders": 1,
                "leechers": 1,
                "size": 1,
            },
            {"url": "url"},
        )

        self.cache_db_con.action("DELETE FROM results")
        query = "INSERT OR IGNORE INTO results ({col}) VALUES ({rep})".format(col=", ".join(self.record[0].keys()), rep=", ".join(["?"] * len(self.record[0])))
        self.cache_db_con.action(query, list(self.record[0].values()))

    def test_mass_upsert(self):
        def num_rows():
            return len(self.cache_db_con.select("SELECT url FROM results"))

        assert num_rows() == 1, num_rows()

        assert self.cache_db_con.upsert("results", self.record[0], self.record[1])
        assert num_rows() == 1, num_rows()

        assert self.cache_db_con.mass_upsert("results", [self.record], log_transaction=True)
        assert num_rows() == 1

        self.record[0]["url"] = self.record[1]["url"] = "new_url"

        assert self.cache_db_con.upsert("results", self.record[0], self.record[1])
        assert num_rows() == 2

        assert self.cache_db_con.mass_upsert("results", [self.record], log_transaction=True)
        assert num_rows() == 2

        assert self.cache_db_con.upsert("results", self.record[0], self.record[1])
        assert num_rows() == 2

        self.record[0]["url"] = self.record[1]["url"] = "third_url"
        self.record[0]["seeders"] = 9999
        assert self.cache_db_con.mass_upsert("results", [self.record], log_transaction=True)
        assert num_rows() == 3

        assert self.cache_db_con.upsert("results", self.record[0], self.record[1])
        assert num_rows() == 3

        assert self.cache_db_con.mass_upsert("results", [self.record], log_transaction=True)
        assert num_rows() == 3

        results = self.cache_db_con.select("SELECT * FROM results WHERE url = ?", [self.record[1]["url"]])

        assert len(results) == 1
        assert results[0]["url"] == self.record[0]["url"]
        assert results[0]["seeders"] == self.record[0]["seeders"]

        results = self.cache_db_con.select("SELECT * FROM results WHERE url = 'url'")
        assert len(results) == 1
        assert results[0]["url"] == "url"
        assert results[0]["url"] != self.record[0]["url"]

        assert results[0]["seeders"] == 1
        assert results[0]["seeders"] != self.record[0]["seeders"]

        assert num_rows() == 3

    def test_upsert_inserts_when_update_misses_after_other_writes(self):
        self.cache_db_con.action("UPDATE results SET seeders = seeders")
        row = dict(self.record[0])
        row["url"] = "race-url"
        assert self.cache_db_con.upsert("results", row, {"url": "race-url"})
        found = self.cache_db_con.select("SELECT url FROM results WHERE url = ?", ["race-url"])
        assert len(found) == 1

    def test_upsert_inserts_when_there_is_no_key(self):
        row = dict(self.record[0])
        row["url"] = "nokey-url"
        assert self.cache_db_con.upsert("results", row, {})
        found = self.cache_db_con.select("SELECT url FROM results WHERE url = ?", ["nokey-url"])
        assert len(found) == 1

    def test_mass_upsert_writes_two_rows_in_one_transaction(self):
        updated = (dict(self.record[0]), {"url": "url"})
        updated[0]["seeders"] = 42
        added = (dict(self.record[0]), {"url": "batch-new"})
        added[0]["url"] = "batch-new"
        added[0]["seeders"] = 7

        traced = []
        self.cache_db_con.connection.set_trace_callback(traced.append)
        try:
            assert self.cache_db_con.mass_upsert("results", [updated, added])
        finally:
            self.cache_db_con.connection.set_trace_callback(None)

        assert sum(1 for statement in traced if statement.strip().upper() == "COMMIT") == 1
        original = self.cache_db_con.select("SELECT seeders FROM results WHERE url = ?", ["url"])
        new_row = self.cache_db_con.select("SELECT seeders FROM results WHERE url = ?", ["batch-new"])
        assert len(original) == 1 and original[0]["seeders"] == 42
        assert len(new_row) == 1 and new_row[0]["seeders"] == 7

    def test_mass_upsert_replace_same_release_keeps_one_url(self):
        self.cache_db_con.action("UPDATE results SET time = 50 WHERE url = ?", ["url"])
        first = (dict(self.record[0]), {"url": "path-1"})
        first[0]["url"] = "path-1"
        first[0]["time"] = 100
        second = (dict(self.record[0]), {"url": "path-2"})
        second[0]["url"] = "path-2"
        second[0]["time"] = 200
        second[0]["seeders"] = 1
        older = (dict(self.record[0]), {"url": "path-old"})
        older[0]["url"] = "path-old"
        older[0]["time"] = 80
        other = (dict(self.record[0]), {"url": "other"})
        other[0]["name"] = "Other.Show.S01E01"
        other[0]["episodes"] = "|2|"
        other[0]["url"] = "other"

        traced = []
        self.cache_db_con.connection.set_trace_callback(traced.append)
        try:
            assert self.cache_db_con.mass_upsert("results", [first, second, older, other], replace_same_release=True)
            lower = (dict(second[0]), {"url": "path-lower"})
            lower[0]["url"] = "path-lower"
            lower[0]["time"] = 150
            lower[0]["seeders"] = 99
            assert self.cache_db_con.mass_upsert("results", [lower], replace_same_release=True)
        finally:
            self.cache_db_con.connection.set_trace_callback(None)

        # The lower-ranked follow-up does not write, so it does not open a second transaction.
        assert sum(1 for statement in traced if statement.strip().upper() == "COMMIT") == 1
        rows = self.cache_db_con.select("SELECT name, url FROM results")
        assert sorted((row["name"], row["url"]) for row in rows) == [
            ("Other.Show.S01E01", "other"),
            ("name", "path-2"),
        ]

    def test_mass_upsert_replace_same_release_equal_time_keeps_later_url(self):
        self.cache_db_con.action("UPDATE results SET time = 100, seeders = 50 WHERE url = ?", ["url"])
        rotated = (dict(self.record[0]), {"url": "path-new"})
        rotated[0]["url"] = "path-new"
        rotated[0]["time"] = 100
        rotated[0]["seeders"] = 1

        assert self.cache_db_con.mass_upsert("results", [rotated], replace_same_release=True)

        rows = self.cache_db_con.select("SELECT url, seeders FROM results")
        assert [(row["url"], row["seeders"]) for row in rows] == [("path-new", 1)]

    def test_stale_release_delete_uses_release_index(self):
        plan = self.cache_db_con.select(
            "EXPLAIN QUERY PLAN DELETE FROM results WHERE provider = ? AND name = ? AND indexerid = ? AND season = ? AND episodes = ? AND url != ?",
            ["provider", "name", 1, 1, "|1|", "other"],
        )
        detail = " ".join(" ".join(str(value) for value in row) for row in plan)
        assert "idx_results_release" in detail
        assert self.cache_db_con.select("SELECT url FROM results WHERE url = ?", ["url"])


if __name__ == "__main__":
    print("==================")
    print("STARTING - DB TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(DBBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    # suite = unittest.TestLoader().loadTestsFromTestCase(DBMultiTests)
    # unittest.TextTestRunner(verbosity=2).run(suite)
