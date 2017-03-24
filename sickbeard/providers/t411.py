# coding=utf-8
# Author: djoole <bobby.djoole@gmail.com>
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

from __future__ import print_function, unicode_literals

from requests.auth import AuthBase
import six
import time
import traceback

from sickbeard import logger, tvcache
from sickrage.helper.common import try_int
from sickrage.helper.common import convert_size
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class T411Provider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "T411")

        self.username = None
        self.password = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = tvcache.TVCache(self, min_time=10)  # Only poll T411 every 10 minutes max

        self.urls = {'base_url': 'https://www.t411.li/',
                     'search': 'https://api.t411.li/torrents/search/%s*?cid=%s&limit=100',
                     'rss': 'https://api.t411.li/torrents/top/today',
                     'login_page': 'https://api.t411.li/auth',
                     'download': 'https://api.t411.li/torrents/download/%s'}

        self.url = self.urls['base_url']

        self.subcategories = [433, 637, 455, 639]

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def login(self):

        if self.token and self.tokenLastUpdate and time.time() < (self.tokenLastUpdate + 30 * 60):
            return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.get_url(self.urls['login_page'], post_data=login_params, returns='json', verify=False)
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if response and 'token' in response:
            self.token = response['token']
            logger.log(type(self.token), logger.ERROR)
            self.tokenLastUpdate = time.time()
            self.session.auth = T411Auth(self.token)
            return True
        else:
            logger.log("Token not found in authentication response", logger.WARNING)
            return False

    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []
        if not self.login():
            return results

        for mode in search_params:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_urlS = ([self.urls['search'] % (search_string, u) for u in self.subcategories], [self.urls['rss']])[mode == 'RSS']
                for search_url in search_urlS:
                    data = self.get_url(search_url, returns='json', verify=False)
                    if not data:
                        continue

                    try:
                        if 'torrents' not in data and mode != 'RSS':
                            logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrents = data['torrents'] if mode != 'RSS' else data

                        if not torrents:
                            logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for torrent in torrents:
                            if mode == 'RSS' and 'category' in torrent and try_int(torrent['category'], 0) not in self.subcategories:
                                continue

                            try:
                                title = torrent['name']
                                torrent_id = torrent['id']
                                download_url = (self.urls['download'] % torrent_id).encode('utf8')
                                if not all([title, download_url]):
                                    continue

                                seeders = try_int(torrent['seeders'])
                                leechers = try_int(torrent['leechers'])
                                verified = bool(torrent['isVerified'])
                                torrent_size = torrent['size']

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode != 'RSS':
                                        logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                    continue

                                if self.confirmed and not verified and mode != 'RSS':
                                    logger.log("Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                                    continue

                                size = convert_size(torrent_size) or -1
                                item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}
                                if mode != 'RSS':
                                    logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                                items.append(item)

                            except Exception:
                                logger.log("Invalid torrent data, skipping result: {0}".format(torrent), logger.DEBUG)
                                logger.log("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.DEBUG)
                                continue

                    except Exception:
                        logger.log("Failed parsing provider. Traceback: {0}".format(traceback.format_exc()), logger.ERROR)

            # For each search mode sort all the items by seeders if available if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results


class T411Auth(AuthBase):  # pylint: disable=too-few-public-methods
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        if isinstance(token, six.text_type):
            self.token = token.encode('utf-8')
        else:
            self.token = token

    def __call__(self, r):
        r.headers[b'Authorization'] = self.token
        return r

provider = T411Provider()
