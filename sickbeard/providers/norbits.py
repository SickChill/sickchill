# coding=utf-8
'''A Norbits (https://norbits.net) provider'''

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

from requests.compat import urlencode

from sickbeard import logger, tvcache

from sickrage.helper.exceptions import AuthException
from sickrage.providers.torrent.TorrentProvider import TorrentProvider

try:
    import json
except ImportError:
    import simplejson as json


class NorbitsProvider(TorrentProvider): # pylint: disable=too-many-instance-attributes
    '''Main provider object'''

    def __init__(self):
        ''' Initialize the class '''
        TorrentProvider.__init__(self, 'Norbits')

        self.username = None
        self.passkey = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = tvcache.TVCache(self, min_time=20)  # only poll Norbits every 15 minutes max

        self.url = 'https://norbits.net'
        self.urls = {'search': self.url + '/api2.php?action=torrents',
                     'download': self.url + '/download.php?'}

        self.logger = logger.Logger()

    def _check_auth(self):

        if not self.username or not self.passkey:
            raise AuthException(('Your authentication credentials for %s are '
                                 'missing, check your config.') % self.name)

        return True

    def _checkAuthFromData(self, parsed_json):  # pylint: disable=invalid-name
        ''' Check that we are authenticated. '''

        if 'status' in parsed_json and 'message' in parsed_json:
            if parsed_json.get('status') == 3:
                self.logger.log((u'Invalid username or password. '
                                 'Check your settings'), logger.WARNING)

        return True

    def search(self, search_params, age=0, ep_obj=None): # pylint: disable=too-many-locals
        ''' Do the actual searching and JSON parsing'''

        results = []

        for mode in search_params:
            items = []
            self.logger.log(u'Search Mode: {}'.format(mode), logger.DEBUG)

            for search_string in search_params[mode]:
                if mode != 'RSS':
                    self.logger.log('Search string: {}'.format(search_string.decode('utf-8')),
                                    logger.DEBUG)

                post_data = {
                    'username': self.username,
                    'passkey': self.passkey,
                    'category': '2', # TV Category
                    'search': search_string,
                }

                self._check_auth()
                parsed_json = self.get_url(self.urls['search'],
                                           post_data=json.dumps(post_data),
                                           json=True)

                if not parsed_json:
                    return []

                if self._checkAuthFromData(parsed_json):
                    if parsed_json and 'data' in parsed_json:
                        json_items = parsed_json['data']
                    else:
                        self.logger.log((u'Resulting JSON from provider is not correct, '
                                         'not parsing it'), logger.ERROR)
                    if 'torrents' in json_items:
                        for item in json_items['torrents']:
                            seeders = item['seeders']
                            leechers = item['leechers']
                            title = item['name']
                            info_hash = item['info_hash']
                            size = item['size']
                            download_url = ('{}{}'.format(self.urls['download'],
                                                          urlencode({'id': item['id'],
                                                                     'passkey': self.passkey})))

                            if seeders < self.minseed or leechers < self.minleech:
                                self.logger.log((u'Discarding torrent because it does not meet '
                                                 'the minimum seeders or leechers: '
                                                 '{} (S:{} L:{})').format
                                                (title, seeders, leechers), logger.DEBUG)
                                continue
                            else:
                                item = title, download_url, size, seeders, leechers, info_hash
                                if mode != "RSS":
                                    self.logger.log((u'Found result: {} with {} seeders and {}'
                                                     'leechers').format(title,
                                                                        seeders,
                                                                        leechers), logger.DEBUG)

                                items.append(item)
            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda tup: tup[3], reverse=True)

            results += items

        return results

    def seed_ratio(self):
        return self.ratio

provider = NorbitsProvider()  # pylint: disable=invalid-name
