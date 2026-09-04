"""Phase 0: cache.db scene_names must not grow duplicate (indexer_id, name) rows."""

from __future__ import annotations

import unittest

from sickchill.oldbeard import db, name_cache
from tests import conftest


class TestSceneNamesUnique(conftest.SickChillTestDBCase):
    INDEXER_ID = 999901
    NAME = "phase0uniquescenename"

    def setUp(self):
        super().setUp()
        self.cache_db = db.DBConnection("cache.db")
        self.cache_db.action("DELETE FROM scene_names WHERE indexer_id = ?", [self.INDEXER_ID])
        # Keep in-memory cache consistent with DB cleanup
        with name_cache.name_cache_lock:
            name_cache.name_cache.pop(self.NAME, None)
            names = name_cache.names_by_indexer.get(self.INDEXER_ID)
            if names is not None:
                names.discard(self.NAME)
                if not names:
                    name_cache.names_by_indexer.pop(self.INDEXER_ID, None)

    def tearDown(self):
        self.cache_db.action("DELETE FROM scene_names WHERE indexer_id = ?", [self.INDEXER_ID])
        with name_cache.name_cache_lock:
            name_cache.name_cache.pop(self.NAME, None)
            names = name_cache.names_by_indexer.get(self.INDEXER_ID)
            if names is not None:
                names.discard(self.NAME)
                if not names:
                    name_cache.names_by_indexer.pop(self.INDEXER_ID, None)
        super().tearDown()

    def test_unique_index_exists(self):
        self.assertTrue(self.cache_db.has_index("idx_scene_names_indexer_name"))
        self.assertGreaterEqual(self.cache_db.get_db_version(), 5)

    def test_insert_or_replace_does_not_duplicate(self):
        self.cache_db.action(
            "INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)",
            [self.INDEXER_ID, self.NAME],
        )
        self.cache_db.action(
            "INSERT OR REPLACE INTO scene_names (indexer_id, name) VALUES (?, ?)",
            [self.INDEXER_ID, self.NAME],
        )
        rows = self.cache_db.select(
            "SELECT COUNT(*) AS c FROM scene_names WHERE indexer_id = ? AND name = ?",
            [self.INDEXER_ID, self.NAME],
        )
        self.assertEqual(rows[0]["c"], 1)

    def test_add_name_and_save_all_do_not_duplicate(self):
        name_cache.add_name(self.NAME, self.INDEXER_ID)
        # Second add_name is a no-op (already in memory)
        name_cache.add_name(self.NAME, self.INDEXER_ID)
        name_cache.save_all_cached_names()
        name_cache.save_all_cached_names()
        rows = self.cache_db.select(
            "SELECT COUNT(*) AS c FROM scene_names WHERE indexer_id = ? AND name = ?",
            [self.INDEXER_ID, self.NAME],
        )
        self.assertEqual(rows[0]["c"], 1)

    def test_dedupe_sql_collapses_preexisting_duplicates(self):
        """The migration DELETE keeps MIN(rowid) per (indexer_id, name)."""
        # Temporarily allow duplicates by inserting via a path that bypasses unique:
        # drop unique index, insert dups, run dedupe SQL, recreate index.
        self.cache_db.action("DROP INDEX IF EXISTS idx_scene_names_indexer_name")
        try:
            for _ in range(5):
                self.cache_db.action(
                    "INSERT INTO scene_names (indexer_id, name) VALUES (?, ?)",
                    [self.INDEXER_ID, self.NAME],
                )
            before = self.cache_db.select(
                "SELECT COUNT(*) AS c FROM scene_names WHERE indexer_id = ? AND name = ?",
                [self.INDEXER_ID, self.NAME],
            )[0]["c"]
            self.assertGreaterEqual(before, 5)

            self.cache_db.action("DELETE FROM scene_names WHERE rowid NOT IN (SELECT MIN(rowid) FROM scene_names GROUP BY indexer_id, name)")
            after = self.cache_db.select(
                "SELECT COUNT(*) AS c FROM scene_names WHERE indexer_id = ? AND name = ?",
                [self.INDEXER_ID, self.NAME],
            )[0]["c"]
            self.assertEqual(after, 1)
        finally:
            self.cache_db.action("CREATE UNIQUE INDEX IF NOT EXISTS idx_scene_names_indexer_name ON scene_names (indexer_id, name)")


if __name__ == "__main__":
    unittest.main()
