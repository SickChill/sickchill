"""
Test tv
"""

import unittest

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

    @staticmethod
    def test_get_episode():
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
        # TODO: implement


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
