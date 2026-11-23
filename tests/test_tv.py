"""
Test tv
"""

import unittest
from unittest.mock import MagicMock, patch

from sickchill import settings
from sickchill.tv import TVEpisode, TVShow
from tests import conftest


class TVShowTests(conftest.SickChillTestPostProcessorCase):
    """
    Test tv shows
    """

    def setUp(self):
        """
        Set up tests
        """
        super().setUp()

    def test_init_indexerid(self):
        """
        test init indexer id
        """
        self.show.load_from_db()
        assert self.show.indexerid == 1

    def test_change_indexerid(self):
        """
        test change indexer id
        """
        self.show.load_from_db()
        assert self.show.indexerid == 1

        self.show.indexerid = 295759
        self.show.save_to_db()
        self.show.load_from_db()

        assert self.show.indexerid == 295759

    def test_set_name(self):
        """
        test set name
        """
        self.show.name = "newName"

        self.show.save_to_db()
        self.show.load_from_db()
        assert self.show.name == "newName"
        assert self.show.show_name == "newName"

        self.show.show_name = "show_name"

        self.show.save_to_db()
        self.show.load_from_db()
        assert self.show.name == "show_name"

    def test_show_with_custom_name(self):
        """
        test set custom name
        """
        self.show.name = "show name"
        self.show.show_name = "show name"
        self.show.custom_name = "newName"
        self.show.save_to_db()
        self.show.load_from_db()

        assert self.show.show_name == "show name"

        assert self.show.custom_name == "newName"
        assert self.show.name == "newName"


class TVEpisodeTests(conftest.SickChillTestDBCase):
    """
    Test tv episode
    """

    def setUp(self):
        """
        Set up
        """
        super().setUp()
        settings.show_list = []

    def test_init_empty_db(self):
        """
        test init empty db
        """
        show = TVShow(1, 1, "en")
        episode = TVEpisode(show, 1, 1)
        episode.name = "asdasdasdajkaj"
        episode.save_to_db()
        episode.load_from_db(1, 1)
        assert episode.name == "asdasdasdajkaj"


class TVTests(conftest.SickChillTestDBCase):
    """
    Test tv
    """

    def setUp(self):
        """
        Set up
        """
        super().setUp()
        settings.show_list = []

    def test_network_logo_name(self):
        """
        Network logos are unidecode(network).lower(), with /:\\ turned into spaces
        so the filename matches sc_network_timezones collectors and is valid on disk.
        """
        show = TVShow(1, 1, "en")
        show.network = "CBS"
        assert show.network_logo_name == "cbs"
        assert show.network_image_url == "images/network/cbs.png"

        show.network = "13ème Rue"
        assert show.network_logo_name == "13eme rue"
        assert show.network_image_url == "images/network/13eme rue.png"

        show.network = "MTV (AU/NZ)"
        assert show.network_logo_name == "mtv (au nz)"
        assert show.network_image_url == "images/network/mtv (au nz).png"

        show.network = "Instagram / IGTV"
        assert show.network_logo_name == "instagram igtv"

        show.network = None
        assert show.network_logo_name == "nonetwork"
        assert show.network_image_url == "images/network/nonetwork.png"

        show.network = "Інтер"
        assert show.network_logo_name == "inter"

    def test_get_episode(self):
        """
        Test get episodes
        """
        show = TVShow(1, 1, "en")
        show.name = "show name"
        show.network = "cbs"
        show.genre = ["crime"]
        show.runtime = 40
        show.status = "Ended"
        show.default_ep_status = "5"
        show.airs = "monday"
        show.startyear = 1987
        show.save_to_db()
        settings.show_list = [show]

        episode = TVEpisode(show, 1, 1)
        episode.name = "Pilot"
        episode.save_to_db()

        def specify_from_db(self, season, episode_number, allow_indexer=True, db_row=None):
            # Local DB load only (conftest stubs specify_episode to avoid indexer I/O).
            _ = allow_indexer
            assert self.load_from_db(season, episode_number, row=db_row)

        # Empty cache → get_episode must populate from DB via specify_episode.
        show.episodes = {}
        with patch.object(TVEpisode, "specify_episode", specify_from_db):
            loaded = show.get_episode(1, 1)
            assert loaded is not None
            assert loaded.season == 1
            assert loaded.episode == 1
            assert loaded.show is show
            assert loaded.name == "Pilot"

            # Second call returns the cached instance.
            assert show.get_episode(1, 1) is loaded
            assert show.episodes[1][1] is loaded

    def _db_episode_row(self, show):
        return {"season": 1, "episode": 1, "showid": show.indexerid, "show_name": show.name}

    def test_load_episodes_from_db_skips_dirty_cached_episode(self):
        show = TVShow(1, 91)
        show.name = "Dirty Skip"
        episode = TVEpisode(show, 1, 1)
        episode.dirty = True
        episode.lock = MagicMock()
        show.episodes[1] = {1: episode}
        row = self._db_episode_row(show)

        with patch("sickchill.tv.db.DBConnection") as connection, patch.object(episode, "load_from_db") as reload:
            connection.return_value.select.return_value = [row]
            scanned = show.load_episodes_from_db()

        episode.lock.__enter__.assert_called_once()
        reload.assert_not_called()
        self.assertTrue(scanned[1][1])

    def test_load_episodes_from_db_reloads_clean_cached_episode(self):
        show = TVShow(1, 92)
        show.name = "Clean Reload"
        episode = TVEpisode(show, 1, 1)
        episode.dirty = False
        episode.lock = MagicMock()
        show.episodes[1] = {1: episode}
        row = self._db_episode_row(show)

        with patch("sickchill.tv.db.DBConnection") as connection, patch.object(episode, "load_from_db", return_value=True) as reload:
            connection.return_value.select.return_value = [row]
            scanned = show.load_episodes_from_db()

        episode.lock.__enter__.assert_called_once()
        reload.assert_called_once_with(1, 1, row=row)
        self.assertTrue(scanned[1][1])

    def _run_indexer_batch(self, show, episode, rows, cursor, sql, get_sql_calls):
        episode.dirty = True
        show.episodes[1] = {episode.episode: episode}
        show.save_to_db = MagicMock()
        indexer = MagicMock()
        indexer.name = "TVDB"
        indexer.episodes.return_value = [{"airedSeason": 1, "airedEpisodeNumber": episode.episode}]
        indexers = MagicMock()
        indexers.__getitem__.return_value = indexer
        preload = MagicMock()
        preload.select.return_value = rows
        writer = MagicMock()
        writer.mass_action.return_value = [cursor]

        with (
            patch("sickchill.tv.sickchill.indexer", indexers),
            patch("sickchill.tv.db.DBConnection", side_effect=[preload, writer]),
            patch.object(episode, "load_from_indexer", return_value=True),
            patch.object(episode, "get_sql", return_value=sql) as get_sql,
        ):
            show.load_episodes_from_indexer()

        get_sql.assert_called_once_with(*get_sql_calls[0], **get_sql_calls[1])
        return writer

    def test_indexer_batch_rechecks_a_row_missing_from_the_preload(self):
        show = TVShow(1, 93)
        episode = TVEpisode(show, 1, 1)
        cursor = MagicMock()
        cursor.rowcount = 1
        sql = ["UPDATE tv_episodes SET name = ? WHERE episode_id = ?", ["Pilot", 5]]
        self._run_indexer_batch(show, episode, [], cursor, sql, [(), {}])
        self.assertFalse(episode.dirty)

    def test_indexer_batch_uses_preloaded_row_when_it_exists(self):
        show = TVShow(1, 94)
        episode = TVEpisode(show, 1, 1)
        row = {"season": 1, "episode": 1, "episode_id": 8, "subtitles": ""}
        cursor = MagicMock()
        cursor.rowcount = 1
        sql = ["UPDATE tv_episodes SET name = ? WHERE episode_id = ?", ["Pilot", 8]]
        self._run_indexer_batch(show, episode, [row], cursor, sql, [(), {"existing_row": row}])
        self.assertFalse(episode.dirty)

    def test_indexer_batch_keeps_dirty_when_the_write_misses_or_a_later_edit_arrives(self):
        show = TVShow(1, 95)
        episode = TVEpisode(show, 1, 1)
        cursor = MagicMock()
        cursor.rowcount = 0
        sql = ["INSERT OR IGNORE INTO tv_episodes (name) VALUES (?)", ["Pilot"]]
        self._run_indexer_batch(show, episode, [], cursor, sql, [(), {}])
        self.assertTrue(episode.dirty)

        cursor.rowcount = 1
        generation = episode._mutation

        def write_then_edit(queries):
            episode._mutation = generation + 1
            return [cursor]

        episode.dirty = True
        show.save_to_db = MagicMock()
        indexer = MagicMock()
        indexer.name = "TVDB"
        indexer.episodes.return_value = [{"airedSeason": 1, "airedEpisodeNumber": 1}]
        indexers = MagicMock()
        indexers.__getitem__.return_value = indexer
        preload = MagicMock()
        preload.select.return_value = []
        writer = MagicMock()
        writer.mass_action.side_effect = write_then_edit
        with (
            patch("sickchill.tv.sickchill.indexer", indexers),
            patch("sickchill.tv.db.DBConnection", side_effect=[preload, writer]),
            patch.object(episode, "load_from_indexer", return_value=True),
            patch.object(episode, "get_sql", return_value=sql),
        ):
            show.load_episodes_from_indexer()

        self.assertTrue(episode.dirty)


if __name__ == "__main__":
    print("==================")
    print("STARTING - TV TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TVShowTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TVEpisodeTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TVTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
