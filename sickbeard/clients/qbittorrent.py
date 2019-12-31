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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
from time import sleep

# Third Party Imports
from requests.auth import HTTPDigestAuth
from requests.compat import urljoin

# First Party Imports
import sickbeard
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):

    def __init__(self, host=None, username=None, password=None):

        super(Client, self).__init__('qbittorrent', host, username, password)

        self.url = self.host
        self.session.auth = HTTPDigestAuth(self.username, self.password)
        self.session.headers.update({
            'Origin': self.host,
            'Referer': self.host
        })

    @property
    def api(self):
        try:
            self.url = urljoin(self.host, 'version/api')
            response = self.session.get(self.url, verify=sickbeard.TORRENT_VERIFY_CERT)
            if response.status_code == 401:
                version = None
            else:
                version = int(response.content)
        except Exception:
            version = 1
        return version

    def _get_auth(self):
        if self.api is None:
            return None

        if self.api > 1:
            self.url = urljoin(self.host, 'login')
            data = {'username': self.username, 'password': self.password}
            try:
                self.response = self.session.post(self.url, data=data)
            except Exception:
                return None

        else:
            try:
                self.response = self.session.get(self.host, verify=sickbeard.TORRENT_VERIFY_CERT)
            except Exception:
                return None

        self.session.cookies = self.response.cookies
        self.auth = self.response.content

        return (None, self.auth)[self.response.status_code != 404]

    def _add_torrent_uri(self, result):

        data = {'urls': result.url}

        if self.api > 6:
            if sickbeard.TORRENT_PATH:
                data['savepath'] = sickbeard.TORRENT_PATH

            label = sickbeard.TORRENT_LABEL
            if result.show.is_anime:
                label = sickbeard.TORRENT_LABEL_ANIME

            if label:
                data['category'] = label.replace(' ', '_')

        self.url = urljoin(self.host, 'command/download')
        if self._request(method='post', data=data, cookies=self.session.cookies):
            sleep(2)  # The client always needs to fetch the torrent/magnet
            return self._verify_added(result.hash)
        return False

    def _add_torrent_file(self, result):

        files = {'torrents': (result.name + '.torrent', result.content)}

        data = {}
        if self.api > 6:
            if sickbeard.TORRENT_PATH:
                data['savepath'] = sickbeard.TORRENT_PATH

            label = sickbeard.TORRENT_LABEL
            if result.show.is_anime:
                label = sickbeard.TORRENT_LABEL_ANIME

            if label:
                data['category'] = label.replace(' ', '_')

        self.url = urljoin(self.host, 'command/upload')
        if self._request(method='post', files=files, data=data, cookies=self.session.cookies):
            return self._verify_added(result.hash)
        return False

    def _set_torrent_label(self, result):

        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME

        if 6 < self.api < 10 and label:
            self.url = urljoin(self.host, 'command/setLabel')
            data = {'hashes': result.hash.lower(), 'label': label.replace(' ', '_')}
            return self._request(method='post', data=data, cookies=self.session.cookies)

        elif self.api >= 10 and label:
            self.url = urljoin(self.host, 'command/setCategory')
            data = {'hashes': result.hash.lower(), 'category': label.replace(' ', '_')}
            return self._request(method='post', data=data, cookies=self.session.cookies)

        return True

    def _set_torrent_priority(self, result):

        self.url = urljoin(self.host, 'command/decreasePrio')
        if result.priority == 1:
            self.url = urljoin(self.host, 'command/increasePrio')

        data = {'hashes': result.hash.lower()}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_pause(self, result):

        self.url = urljoin(self.host, 'command/resume')
        if sickbeard.TORRENT_PAUSED:
            self.url = urljoin(self.host, 'command/pause')

        data = {'hash': result.hash.lower()}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _verify_added(self, torrent_hash, attempts=10):
        self.url = urljoin(self.host, 'query/propertiesGeneral/{}'.format(torrent_hash.lower()))
        for i in range(attempts):
            if self._request(method='get', cookies=self.session.cookies):
                if self.response.json()['piece_size'] != -1:
                    return True
            sleep(2)
        return False
