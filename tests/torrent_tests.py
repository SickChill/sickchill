# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.


import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest

import urlparse
import tests.test_lib as test
from bs4 import BeautifulSoup
from sickbeard.helpers import getURL
from sickbeard.tv import TVEpisode, TVShow
import requests

from sickbeard.providers.bitcannon import BitCannonProvider

class TorrentBasicTests(test.SickbeardTestDBCase):

    @classmethod
    def setUpClass(cls):
        cls.shows = []

        show = TVShow(1, 121361)
        show.name = "Italian Works"
        show.episodes = []
        episode = TVEpisode(show, 05, 10)
        episode.name = "Pines of Rome"
        episode.scene_season = 5
        episode.scene_episode = 10
        show.episodes.append(episode)
        cls.shows.append(show)

    def test_bitcannon(self):
        bitcannon = BitCannonProvider()
        bitcannon.custom_url = ""        # true testing requires a valid URL here (e.g., "http://localhost:3000/")
        bitcannon.api_key = ""

        if len(bitcannon.custom_url) > 0:
            search_strings_list = bitcannon._get_episode_search_strings(self.shows[0].episodes[0])  # [{'Episode': ['Italian Works S05E10']}]
            for search_strings in search_strings_list:
                bitcannon._doSearch(search_strings)   # {'Episode': ['Italian Works S05E10']}

        return True

    def test_search(self):
        url = 'http://kickass.to/'
        search_url = 'http://kickass.to/usearch/American%20Dad%21%20S08%20-S08E%20category%3Atv/?field=seeders&sorder=desc'

        html = getURL(search_url, session=requests.Session())
        if not html:
            return

        soup = BeautifulSoup(html, features=["html5lib", "permissive"])

        torrent_table = soup.find('table', attrs={'class': 'data'})
        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

        # cleanup memory
        soup.clear(True)

        #Continue only if one Release is found
        if len(torrent_rows) < 2:
            print "The data returned does not contain any torrents"
            return

        for tr in torrent_rows[1:]:

            try:
                link = urlparse.urljoin(url, (tr.find('div', {'class': 'torrentname'}).find_all('a')[1])['href'])
                _id = tr.get('id')[-7:]
                title = (tr.find('div', {'class': 'torrentname'}).find_all('a')[1]).text \
                    or (tr.find('div', {'class': 'torrentname'}).find_all('a')[2]).text
                url = tr.find('a', 'imagnet')['href']
                verified = True if tr.find('a', 'iverify') else False
                trusted = True if tr.find('img', {'alt': 'verified'}) else False
                seeders = int(tr.find_all('td')[-2].text)
                leechers = int(tr.find_all('td')[-1].text)
            except (AttributeError, TypeError):
                continue

            print title

if __name__ == "__main__":
    print "=================="
    print "STARTING - Torrent Basic TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(TorrentBasicTests)
    unittest.TextTestRunner(verbosity=2).run(suite)
