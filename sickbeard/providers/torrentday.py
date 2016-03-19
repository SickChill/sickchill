# coding=utf-8
# Author: Mr_Orange <mr_orange@hotmail.it>
#
# URL: https://sickrage.github.io
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
from requests.compat import urljoin
from requests.utils import add_dict_to_cookiejar, dict_from_cookiejar

from sickbeard import logger, tvcache

from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentDayProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "TorrentDay")

        # Credentials
        self.username = None
        self.password = None
        self._uid = None
        self._hash = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        # URLs
        self.url = 'https://classic.torrentday.com'
        self.urls = {
            'login': urljoin(self.url, '/torrents/'),
            'search': urljoin(self.url, '/V3/API/API.php'),
            'download': urljoin(self.url, '/download.php/')
        }

        self.cookies = None
        self.categories = {'Season': {'c14': 1}, 'Episode': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1},
                           'RSS': {'c2': 1, 'c26': 1, 'c7': 1, 'c24': 1, 'c14': 1}}

        # Cache
        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll IPTorrents every 10 minutes max

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self._uid and self._hash:
            add_dict_to_cookiejar(self.session.cookies, self.cookies)
        else:

            login_params = {
                'username': self.username,
                'password': self.password,
                'submit.x': 0,
                'submit.y': 0
            }

            response = self.get_url(self.urls['login'], post_data=login_params, returns='text')
            if not response:
                logger.log(u"Unable to connect to provider", logger.WARNING)
                return False

            if re.search('You tried too often', response):
                logger.log(u"Too many login access attempts", logger.WARNING)
                return False

            try:
                if dict_from_cookiejar(self.session.cookies)['uid'] and dict_from_cookiejar(self.session.cookies)['pass']:
                    self._uid = dict_from_cookiejar(self.session.cookies)['uid']
                    self._hash = dict_from_cookiejar(self.session.cookies)['pass']
                    self.cookies = {'uid': self._uid,
                                    'pass': self._hash}
                    return True
            except Exception:
                pass

            logger.log(u"Unable to obtain cookie", logger.WARNING)
            return False

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: {0}".format(search_string.decode("utf-8")),
                               logger.DEBUG)

                search_string = '+'.join(search_string.split())

                post_data = dict({'/browse.php?': None, 'cata': 'yes', 'jxt': 8, 'jxw': 'b', 'search': search_string},
                                 **self.categories[mode])

                if self.freeleech:
                    post_data.update({'free': 'on'})

                parsedJSON = self.get_url(self.urls['search'], post_data=post_data, returns='json')
                if not parsedJSON:
                    logger.log(u"No data returned from provider", logger.DEBUG)
                    continue

                try:
                    torrents = parsedJSON.get('Fs', [])[0].get('Cn', {}).get('torrents', [])
                except Exception:
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                for torrent in torrents:

                    title = re.sub(r"\[.*\=.*\].*\[/.*\]", "", torrent['name']) if torrent['name'] else None
                    download_url = urljoin(self.urls['download'], '{0}/{1}'.format(torrent['id'], torrent['fname'])) if torrent['id'] and torrent['fname'] else None

                    if not all([title, download_url]):
                        continue

                    seeders = int(torrent['seed']) if torrent['seed'] else 1
                    leechers = int(torrent['leech']) if torrent['leech'] else 0

                    # Filter unseeded torrent
                    if seeders < self.minseed or leechers < self.minleech:
                        if mode != 'RSS':
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        continue

                    torrent_size = torrent['size']
                    size = convert_size(torrent_size) or -1

                    item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': None}

                    if mode != 'RSS':
                        logger.log(u"Found result: {0} with {1} seeders and {2} leechers".format
                                   (title, seeders, leechers), logger.DEBUG)

                    items.append(item)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentDayProvider()
