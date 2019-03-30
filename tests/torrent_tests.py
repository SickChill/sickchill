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
Test torrents
"""

# pylint: disable=line-too-long

import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from bs4 import BeautifulSoup
from sickbeard.helpers import getURL, make_session
from sickbeard.providers.bitcannon import BitCannonProvider
from sickbeard.tv import TVEpisode, TVShow
import tests.test_lib as test

from six.moves import urllib


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
            # pylint: disable=protected-access
            search_strings_list = bitcannon._get_episode_search_strings(self.shows[0].episodes[0])  # [{'Episode': ['Italian Works S05E10']}]
            for search_strings in search_strings_list:
                bitcannon.search(search_strings)   # {'Episode': ['Italian Works S05E10']} # pylint: disable=protected-access

        return True

    @staticmethod
    @unittest.skip('KickAssTorrents is down, needs a replacement')  # TODO
    def test_search():  # pylint: disable=too-many-locals
        """
        Test searching
        """
        url = 'http://kickass.to/'
        search_url = 'http://kickass.to/usearch/American%20Dad%21%20S08%20-S08E%20category%3Atv/?field=seeders&sorder=desc'

        html = getURL(search_url, session=make_session(), returns='text')
        if not html:
            return

        soup = BeautifulSoup(html, 'html5lib')

        torrent_table = soup.find('table', attrs={'class': 'data'})
        torrent_rows = torrent_table('tr') if torrent_table else []

        # cleanup memory
        soup.clear(True)

        # Continue only if one Release is found
        if len(torrent_rows) < 2:
            print("The data returned does not contain any torrents")
            return

        for row in torrent_rows[1:]:
            try:
                link = urllib.parse.urljoin(url, (row.find('div', {'class': 'torrentname'})('a')[1])['href'])
                _id = row.get('id')[-7:]
                title = (row.find('div', {'class': 'torrentname'})('a')[1]).text \
                    or (row.find('div', {'class': 'torrentname'})('a')[2]).text
                url = row.find('a', 'imagnet')['href']
                verified = True if row.find('a', 'iverify') else False
                trusted = True if row.find('img', {'alt': 'verified'}) else False
                seeders = int(row('td')[-2].text)
                leechers = int(row('td')[-1].text)
                _ = link, _id, verified, trusted, seeders, leechers
            except (AttributeError, TypeError):
                continue

            print(title)

if __name__ == "__main__":
    print("==================")
    print("STARTING - Torrent Basic TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(TorrentBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
