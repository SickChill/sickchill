# coding=utf-8

# Author: Bill Nasty
# URL: https://github.com/SickRage/SickRage
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import re
import traceback

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider
from urllib import urlencode


class AlphaRatioProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "AlphaRatio")

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'http://alpharatio.cc/',
                     'login': 'http://alpharatio.cc/login.php',
                     'detail': 'http://alpharatio.cc/torrents.php?torrentid=%s',
                     'search': 'http://alpharatio.cc/torrents.php?searchstr=%s%s',
                     'download': 'http://alpharatio.cc/%s'}

        self.url = self.urls['base_url']

        self.categories = "&filter_cat[1]=1&filter_cat[2]=1&filter_cat[3]=1&filter_cat[4]=1&filter_cat[5]=1"

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = AlphaRatioCache(self)

    def login(self):
        login_params = {'username': self.username,
                        'password': self.password,
                        'remember_me': 'on',
                        'login': 'submit'}

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('Invalid Username/password', response) \
                or re.search('<title>Login :: AlphaRatio.cc</title>', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self.login():
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (urlencode(search_string), self.categories)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)

                data = self.get_url(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data, 'html5lib') as html:
                        torrent_table = html.find('table', attrs={'id': 'torrent_table'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')
                            link = result.find('a', attrs={'dir': 'ltr'})
                            url = result.find('a', attrs={'title': 'Download'})

                            try:
                                num_cells = len(cells)
                                title = link.contents[0] if link.contents[0] else None
                                download_url = self.urls['download'] % (url['href']) if url['href'] else None
                                seeders = cells[num_cells - 2].contents[0] if cells[len(cells) - 2].contents[0] else 1
                                leechers = cells[num_cells - 1].contents[0] if cells[len(cells) - 1].contents[0] else 0
                                torrent_size = cells[len(cells) - 4].contents[0]
                                size = convert_size(torrent_size) or -1
                            except (AttributeError, TypeError, KeyError, ValueError):
                                continue

                            if not all([title, download_url]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers
                            if mode != 'RSS':
                                logger.log(u"Found result: %s " % title, logger.DEBUG)

                            items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.WARNING)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class AlphaRatioCache(tvcache.TVCache):

    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll AlphaRatio every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider.search(search_strings)}

provider = AlphaRatioProvider()
