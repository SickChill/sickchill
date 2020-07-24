# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

"""
Test tv
"""

# Stdlib Imports
import unittest

# First Party Imports
from sickbeard.tv import TVEpisode, TVShow
from sickchill import settings
from tests import test_lib as test


class TVShowTests(test.SickbeardTestDBCase):
    """
    Test tv shows
    """
    def setUp(self):
        """
        Set up tests
        """
        super(TVShowTests, self).setUp()
        settings.showList = []

    def test_init_indexerid(self):
        """
        test init indexer id
        """
        show = TVShow(1, 1, "en")
        self.assertEqual(show.indexerid, 1)

    def test_change_indexerid(self):
        """
        test change indexer id
        """
        show = TVShow(1, 257655, "en")
        show.name = "show name"
        show.network = "cbs"
        show.genre = ["crime"]
        show.runtime = 40
        show.status = "Ended"
        show.default_ep_status = "5"
        show.airs = "monday"
        show.startyear = 1987

        show.saveToDB()
        show.loadFromDB()

        show.indexerid = 295759
        show.saveToDB()
        show.loadFromDB()

        self.assertEqual(show.indexerid, 295759)

    def test_set_name(self):
        """
        test set name
        """
        show = TVShow(1, 1, "en")
        show.name = "newName"
        show.saveToDB()
        show.loadFromDB()
        self.assertEqual(show.name, "newName")


class TVEpisodeTests(test.SickbeardTestDBCase):
    """
    Test tv episode
    """
    def setUp(self):
        """
        Set up
        """
        super(TVEpisodeTests, self).setUp()
        settings.showList = []

    def test_init_empty_db(self):
        """
        test init empty db
        """
        show = TVShow(1, 1, "en")
        episode = TVEpisode(show, 1, 1)
        episode.name = "asdasdasdajkaj"
        episode.saveToDB()
        episode.loadFromDB(1, 1)
        self.assertEqual(episode.name, "asdasdasdajkaj")


class TVTests(test.SickbeardTestDBCase):
    """
    Test tv
    """
    def setUp(self):
        """
        Set up
        """
        super(TVTests, self).setUp()
        settings.showList = []

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
        show.saveToDB()
        settings.showList = [show]
        # TODO: implement


if __name__ == '__main__':
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
