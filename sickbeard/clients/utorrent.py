# coding=utf-8

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

from __future__ import unicode_literals

import re
from collections import OrderedDict

import six
from requests.compat import urljoin

import sickbeard
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        """
        Initializes the utorrent client class and sets the url, username, and password
        """
        super(Client, self).__init__('uTorrent', host, username, password)
        self.url = urljoin(self.host, 'gui/')

    def _request(self, method='get', params=None, data=None, files=None, cookies=None):  # pylint: disable=too-many-arguments
        """
        Overrides the parent _request method to add the auth token
        """
        ordered_params = OrderedDict({'token': self.auth})
        for k, v in six.iteritems(params) or {}:
            ordered_params.update({k: v})

        return super(Client, self)._request(method=method, params=ordered_params, data=data, files=files, cookies=cookies)

    def _get_auth(self):
        """
        Makes a request to the token url to get a CSRF token
        """
        try:
            self.response = self.session.get(urljoin(self.url, 'token.html'), verify=False)
            self.response.raise_for_status()
            self.auth = re.findall("<div.*?>(.*?)</", self.response.text)[0]
        except Exception as error:
            sickbeard.helpers.handle_requests_exception(error)
            self.auth = None

        return self.auth

    def _add_torrent_uri(self, result):
        """
        Adds a torrent either by magnet or url
        params: :result: an instance of the searchResult class
        """
        params = {'action': 'add-url', 's': result.url}
        return self._request(params=params)

    def _add_torrent_file(self, result):
        """
        Adds a torrent file from memory
        params: :result: an instance of the searchResult class
        """
        params = {'action': 'add-file'}
        files = {'torrent_file': (result.name + '.torrent', result.content)}
        return self._request(method='post', params=params, files=files)

    def _set_torrent_label(self, result):
        """
        Sets a label on an existing torrent in the client
        params: :result: an instance of the searchResult class
        """
        label = sickbeard.TORRENT_LABEL_ANIME or sickbeard.TORRENT_LABEL if result.show.is_anime else sickbeard.TORRENT_LABEL
        params = {
            'action': 'setprops',
            'hash': result.hash,
            's': 'label',
            'v': label
        }
        return self._request(params=params)

    def _set_torrent_ratio(self, result):
        """
        Sets the desired seed ratio for an existing torrent in the client
        params: :result: an instance of the searchResult class
        """
        if result.ratio in (None, ''):
            return True

        params = {
            'action': 'setprops',
            'hash': result.hash,
            's': 'seed_override',
            'v': '1'
        }
        if not self._request(params=params):
            return False

        params = {
            'action': 'setprops',
            'hash': result.hash,
            's': 'seed_ratio',
            'v': float(result.ratio) * 10
        }
        return self._request(params=params)

    def _set_torrent_seed_time(self, result):
        """
        Sets the amount of time a torrent that exists in the client should seed for
        params: :result: an instance of the searchResult class
        """
        if not sickbeard.TORRENT_SEED_TIME:
            return True

        params = {
            'action': 'setprops',
            'hash': result.hash,
            's': 'seed_override',
            'v': '1'}

        if not self._request(params=params):
            return False

        params = {
            'action': 'setprops',
            'hash': result.hash,
            's': 'seed_time',
            'v': 3600 * float(sickbeard.TORRENT_SEED_TIME)
        }
        return self._request(params=params)

    def _set_torrent_priority(self, result):
        """
        Sets the priority of a torrent that exists in the client
        params: :result: an instance of the searchResult class
        """
        if not result.priority:
            return True

        params = {'action': 'queuetop', 'hash': result.hash}
        return self._request(params=params)

    def _set_torrent_pause(self, result):
        """
        Pauses a torrent that exists on the client
        params: :result: an instance of the searchResult class
        """
        params = {
            'action': 'pause' if sickbeard.TORRENT_PAUSED else 'start',
            'hash': result.hash
        }
        return self._request(params=params)
