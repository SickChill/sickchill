# -*- coding: latin-1 -*-
# Author: djoole <bobby.djoole@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import time
import traceback
from requests.auth import AuthBase

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic


class T411Provider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "T411")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.token = None
        self.tokenLastUpdate = None

        self.cache = T411Cache(self)

        self.urls = {'base_url': 'http://www.t411.in/',
                     'search': 'https://api.t411.in/torrents/search/%s?cid=%s&limit=100',
                     'rss': 'https://api.t411.in/torrents/top/today',
                     'login_page': 'https://api.t411.in/auth',
                     'download': 'https://api.t411.in/torrents/download/%s'}

        self.url = self.urls['base_url']

        self.subcategories = [433, 637, 455, 639]

        self.minseed = 0
        self.minleech = 0
        self.confirmed = False

    def _doLogin(self):

        if self.token is not None:
            if time.time() < (self.tokenLastUpdate + 30 * 60):
                return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.urls['login_page'], post_data=login_params, timeout=30, json=True)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if response and 'token' in response:
            self.token = response['token']
            self.tokenLastUpdate = time.time()
            self.uid = response['uid'].encode('ascii', 'ignore')
            self.session.auth = T411Auth(self.token)
            return True
        else:
            logger.log(u"Token not found in authentication response", logger.WARNING)
            return False

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURLS = ([self.urls['search'] % (search_string, u) for u in self.subcategories], [self.urls['rss']])[mode is 'RSS']
                for searchURL in searchURLS:
                    logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                    data = self.getURL(searchURL, json=True)
                    if not data:
                        continue

                    try:
                        if 'torrents' not in data and mode is not 'RSS':
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        torrents = data['torrents'] if mode is not 'RSS' else data

                        if not torrents:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        for torrent in torrents:
                            if mode is 'RSS' and int(torrent['category']) not in self.subcategories:
                                continue

                            try:
                                title = torrent['name']
                                torrent_id = torrent['id']
                                download_url = (self.urls['download'] % torrent_id).encode('utf8')
                                if not all([title, download_url]):
                                    continue

                                size = int(torrent['size'])
                                seeders = int(torrent['seeders'])
                                leechers = int(torrent['leechers'])
                                verified = bool(torrent['isVerified'])

                                # Filter unseeded torrent
                                if seeders < self.minseed or leechers < self.minleech:
                                    if mode is not 'RSS':
                                        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                    continue

                                if self.confirmed and not verified and mode is not 'RSS':
                                    logger.log(u"Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                                    continue

                                item = title, download_url, size, seeders, leechers
                                if mode is not 'RSS':
                                    logger.log(u"Found result: %s " % title, logger.DEBUG)

                                items[mode].append(item)

                            except Exception:
                                logger.log(u"Invalid torrent data, skipping result: %s" % torrent, logger.DEBUG)
                                logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.DEBUG)
                                continue

                    except Exception:
                        logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class T411Auth(AuthBase):
    """Attaches HTTP Authentication to the given Request object."""
    def __init__(self, token):
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = self.token
        return r


class T411Cache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll T411 every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}


provider = T411Provider()
