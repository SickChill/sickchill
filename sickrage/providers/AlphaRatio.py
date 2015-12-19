# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

import re
import traceback

from sickbeard import logger
from sickbeard.bs4_parser import BS4Parser
from sickbeard.tvcache import TVCache
from sickrage.providers.TorrentProvider import TorrentProvider


class AlphaRatioProvider(TorrentProvider):
    def __init__(self):
        TorrentProvider.__init__(self, 'AlphaRatio')

        self.cache = AlphaRatioCache(self)
        self.categories = '&filter_cat[1]=1&filter_cat[2]=1&filter_cat[3]=1&filter_cat[4]=1&filter_cat[5]=1'
        self.minleech = None
        self.minseed = None
        self.password = None
        self.proper_strings = ['PROPER', 'REPACK']
        self.ratio = None
        self.urls = {
            'base_url': 'http://alpharatio.cc/',
            'detail': 'http://alpharatio.cc/torrents.php?torrentid=%s',
            'download': 'http://alpharatio.cc/%s',
            'login': 'http://alpharatio.cc/login.php',
            'search': 'http://alpharatio.cc/torrents.php?searchstr=%s%s',
        }
        self.url = self.urls['base_url']
        self.username = None

    def login(self):
        login_params = {
            'login': 'submit',
            'password': self.password,
            'remember_me': 'on',
            'username': self.username,
        }

        response = self.get_url(self.urls['login'], post_data=login_params, timeout=30)

        if not response:
            logger.log(u'Unable to connect to %s' % self.name, logger.WARNING)
            return False

        if re.search('Invalid Username/password', response) \
                or re.search('<title>Login :: AlphaRatio.cc</title>', response):
            logger.log(u'Invalid username or password. Check your settings for %s' % self.name, logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):
        results = []
        items = {
            'Episode': [],
            'RSS': [],
            'Season': [],
        }

        if not self.login():
            return results

        for mode in search_params.keys():
            logger.log(u'Search mode: %s' % mode, logger.DEBUG)

            for search_param in search_params[mode]:
                if mode != 'RSS':
                    logger.log(u'Search string: %s' % search_param, logger.DEBUG)

                search_url = self.urls['search'] % (search_param, self.categories)

                logger.log(u'Search URL: %s' % search_url, logger.DEBUG)

                response = self.get_url(search_url)

                if not response:
                    continue

                try:
                    with BS4Parser(response, 'html5lib') as html:
                        torrent_table = html.find('table', attrs={'id': 'torrent_table'})
                        torrent_rows = torrent_table.find_all('tr') if torrent_table else []

                        # Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.log(u'Data returned from %s does not contain any torrents' % self.name, logger.DEBUG)
                            continue

                        for result in torrent_rows[1:]:
                            cells = result.find_all('td')
                            link = result.find('a', attrs={'dir': 'ltr'})
                            url = result.find('a', attrs={'title': 'Download'})

                            try:
                                title = link.contents[0]
                                download_url = self.urls['download'] % (url['href'])
                                seeders = cells[len(cells) - 2].contents[0]
                                leechers = cells[len(cells) - 1].contents[0]
                                # FIXME
                                size = -1
                            except (AttributeError, TypeError):
                                continue

                            if not all([download_url, title]):
                                continue

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != 'RSS':
                                    logger.log(u'Discarding torrent because it doesn\'t meet the minimum seeders or '
                                               u'leechers: %s (S: %s, L: %s))' % (title, seeders, leechers),
                                               logger.DEBUG)
                                continue

                            item = title, download_url, size, seeders, leechers

                            if mode != 'RSS':
                                logger.log(u'Found result: %s' % title, logger.DEBUG)

                            items[mode].append(item)
                except Exception:
                    logger.log(u'Failed parsing %s. Traceback: %s' % (self.name, traceback.format_exc()),
                               logger.WARNING)

            # For each search mode, sort all the items by seeders, if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio


class AlphaRatioCache(TVCache):
    def __init__(self, provider_obj):
        TVCache.__init__(self, provider_obj)

        # Only poll AlphaRatio every 20 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_strings = {
            'RSS': ['']
        }

        return {
            'entries': self.provider.search(search_strings)
        }


provider = AlphaRatioProvider()
