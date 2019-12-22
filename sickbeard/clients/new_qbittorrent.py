# coding=utf-8

# Author: Mr_Orange <mr_orange@hotmail.it>
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

from time import sleep

from requests.auth import HTTPDigestAuth
from requests.compat import urljoin

import sickbeard
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):

    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('qBittorrent APIv2', host, username, password)
        self.url = self.host
        self.api_prefix = 'api/v2/'
        self.session.auth = HTTPDigestAuth(self.username, self.password)
        self.session.headers.update({
            'Origin': self.host,
            'Referer': self.host
        })

    @property
    def api(self):
        try:
            self.url = urljoin(self.host, self.api_prefix + 'app/webapiVersion')
            response = self.session.get(self.url, verify=sickbeard.TORRENT_VERIFY_CERT)
            if response.status_code == 401:
                version = None
            else:
                version = float(response.content)
        except Exception:
            version = 2
        return version

    def _get_auth(self):
        if self.api is None:
            return None
        self.url = urljoin(self.host, self.api_prefix + 'auth/login')
        data = {'username': self.username, 'password': self.password}
        try:
            self.response = self.session.post(self.url, data=data)
        except Exception:
            return None
        self.session.cookies = self.response.cookies
        self.auth = self.response.content
        return (None, self.auth)[self.response.status_code != 403]

    def _add_torrent_uri(self, result):
        data = {'urls': result.url}
        self.url = urljoin(self.host, self.api_prefix + 'torrents/add')
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _add_torrent_file(self, result):
        files = {'torrents': (result.name + '.torrent', result.content)}
        self.url = urljoin(self.host, self.api_prefix + 'torrents/add')
        return self._request(method='post', files=files, cookies=self.session.cookies)

    def _set_torrent_label(self, result):
        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME
        self.url = urljoin(self.host, self.api_prefix + 'torrents/setCategory')
        data = {'hashes': result.hash.lower(), 'category': label.replace(' ', '_')}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_priority(self, result):
        self.url = urljoin(self.host, self.api_prefix + 'torrents/decreasePrio?hashes={}'.format(result.hash.lower))
        if result.priority == 1:
            self.url = urljoin(self.host, self.api_prefix + 'torrents/increasePrio?hashes={}'.format(result.hash.lower))
        return self._request(method='get', cookies=self.session.cookies)

    def _set_torrent_pause(self, result):
        self.url = urljoin(self.host, self.api_prefix + 'torrents/resume?hashes={}'.format(result.hash.lower()))
        if sickbeard.TORRENT_PAUSED:
            self.url = urljoin(self.host, self.api_prefix + 'torrents/pause?hashes={}'.format(result.hash.lower()))
        return self._request(method='get', cookies=self.session.cookies)

    def _verify_added(self, torrent_hash, attempts=10):
        self.url = urljoin(self.host, self.api_prefix + 'torrents/info?hashes={}'.format(torrent_hash.lower()))
        for i in range(attempts):
            if self._request(method='get', cookies=self.session.cookies):
                if self.response.json()['piece_size'] != -1:
                    return True
            sleep(2)
        return False
