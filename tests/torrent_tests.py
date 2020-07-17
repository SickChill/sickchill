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

# Stdlib Imports
import unittest

# First Party Imports
import sickbeard
from sickbeard.tv import TVEpisode, TVShow
from sickchill.providers.media.torrent import BitCannonProvider, provider as rarbg
from tests import test_lib as test


class TorrentBasicTests(test.SickbeardTestDBCase):
    """
    Test torrents
    """
    @classmethod
    def setUpClass(cls):
        cls.shows = []

        show = TVShow(1, 121361)
        show.name = "Italian Works"
        show.episodes = []
        episode = TVEpisode(show, 5, 10)
        episode.name = "Pines of Rome"
        episode.scene_season = 5
        episode.scene_episode = 10
        show.episodes.append(episode)
        cls.shows.append(show)

    def test_bitcannon(self):
        """
        Test bitcannon
        """
        bitcannon = BitCannonProvider()
        bitcannon.custom_url = ""        # true testing requires a valid URL here (e.g., "http://localhost:3000/")
        bitcannon.api_key = ""

        if bitcannon.custom_url:

            search_strings_list = bitcannon.get_episode_search_strings(self.shows[0].episodes[0])  # [{'Episode': ['Italian Works S05E10']}]
            for search_strings in search_strings_list:
                bitcannon.search(search_strings)  # {'Episode': ['Italian Works S05E10']}

        return True

    @unittest.skip('Only run this manually')
    def test_search(self):
        """
        Test searching, using rarbg
        """
        sickbeard.CPU_PRESET = 'LOW'
        results = rarbg.search({'Episode': ['The Mandalorian S01E08']})
        self.assertTrue(results)
        self.assertIn('Mandalorian', results[0]['title'])

        results = rarbg.search({'RSS': ['']})
        self.assertTrue(results)


if __name__ == "__main__":
    print("==================")
    print("STARTING - Torrent Basic TESTS")
    print("==================")
    print("######################################################################")

    def override_log(msg, *args, **kwargs):
        """Override the SickChill logger so we can see the debug output from providers"""
        _ = args, kwargs
        print(msg)

    sickbeard.logger.info = override_log
    sickbeard.logger.debug = override_log
    sickbeard.logger.error = override_log
    sickbeard.logger.warning = override_log

    SUITE = unittest.TestLoader().loadTestsFromTestCase(TorrentBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
