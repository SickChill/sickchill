# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
#
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

from __future__ import absolute_import, print_function, unicode_literals

# Third Party Imports
from requests.compat import urljoin

# First Party Imports
from sickbeard import logger, tvcache
from sickchill.helper.exceptions import AuthException
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class ShazbatProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, 'Shazbat.tv')

        self.supports_backlog = False

        self.passkey = None
        self.options = None

        self.cache = ShazbatCache(self, min_time=20)

        self.url = 'http://www.shazbat.tv'
        self.urls = {
            'login': urljoin(self.url, 'login'),
            'rss_recent': urljoin(self.url, 'rss/recent'),
            # 'rss_queue': urljoin(self.url, 'rss/download_queue'),
            # 'rss_followed': urljoin(self.url, 'rss/followed')
        }

    def _check_auth(self):
        if not self.passkey:
            raise AuthException('Your authentication credentials are missing, check your config.')

        return True

    def _check_auth_from_data(self, data):
        if not self.passkey:
            self._check_auth()
        elif data.get('bozo') == 1 and not (data['entries'] and data['feed']):
            logger.log('Invalid username or password. Check your settings', logger.WARNING)

        return True


class ShazbatCache(tvcache.TVCache):
    def _get_rss_data(self):
        params = {
            'passkey': self.provider.passkey,
            'fname': 'true',
            'limit': 100,
            'duration': '2 hours'
        }

        return self.get_rss_feed(self.provider.urls['rss_recent'], params=params)

    def _check_auth(self, data):
        return self.provider._check_auth_from_data(data)  # pylint: disable=protected-access

provider = ShazbatProvider()
