# coding=utf-8

# Author: Mr_Orange <mr_orange@hotmail.it>
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

from __future__ import unicode_literals

from time import sleep

import sickbeard
from requests.auth import HTTPDigestAuth
from sickbeard.clients.generic import GenericClient
from sickrage.helper.common import try_int


class qbittorrentAPI(GenericClient):

    def __init__(self, host=None, username=None, password=None):

        super(qbittorrentAPI, self).__init__('qbittorrent', host, username, password)

        self.url = self.host
        self.session.auth = HTTPDigestAuth(self.username, self.password)

    @property
    def api(self):
        try:
            self.url = self.host + 'version/api'
            version = int(self.session.get(self.url, verify=sickbeard.TORRENT_VERIFY_CERT).content)
        except Exception:
            version = 1
        return version

    def _get_auth(self):

        if self.api > 1:
            self.url = self.host + 'login'
            data = {'username': self.username, 'password': self.password}
            try:
                self.response = self.session.post(self.url, data=data)
            except Exception:
                return None

        else:
            try:
                self.response = self.session.get(self.host, verify=sickbeard.TORRENT_VERIFY_CERT)
                self.auth = self.response.content
            except Exception:
                return None

        self.session.cookies = self.response.cookies
        self.auth = self.response.content

        return (None, self.auth)[self.response.status_code != 404]

    def _add_torrent_uri(self, result):

        self.url = self.host + 'command/download'
        data = {'urls': result.url}
        if self._request(method='post', data=data, cookies=self.session.cookies):
            return self._verify_added(result.hash)
        return False

    def _add_torrent_file(self, result):

        self.url = self.host + 'command/upload'
        files = {'torrents': (result.name + '.torrent', result.content)}
        if self._request(method='post', files=files, cookies=self.session.cookies):
            return self._verify_added(result.hash)
        return False

    def _set_torrent_label(self, result):

        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME

        if 6 < self.api < 10 and label:
            self.url = self.host + 'command/setLabel'
            data = {'hashes': result.hash.lower(), 'label': label.replace(' ', '_')}
            return self._request(method='post', data=data, cookies=self.session.cookies)

        elif self.api >= 10 and label:
            self.url = self.host + 'command/setCategory'
            data = {'hashes': result.hash.lower(), 'category': label.replace(' ', '_')}
            return self._request(method='post', data=data, cookies=self.session.cookies)

        return True

    def _set_torrent_priority(self, result):

        self.url = self.host + 'command/decreasePrio'
        if result.priority == 1:
            self.url = self.host + 'command/increasePrio'

        data = {'hashes': result.hash.lower()}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _set_torrent_pause(self, result):

        self.url = self.host + 'command/resume'
        if sickbeard.TORRENT_PAUSED:
            self.url = self.host + 'command/pause'

        data = {'hash': result.hash.lower()}
        return self._request(method='post', data=data, cookies=self.session.cookies)

    def _verify_added(self, torrent_hash, attempts=5):
        self.url = self.host + 'query/propertiesGeneral/' + torrent_hash.lower()
        for i in range(attempts):
            if self._request(method='get', cookies=self.session.cookies):
                if try_int(self.response.headers.get('Content-Length')) > 0:
                    return True
            sleep(2)
        return False

api = qbittorrentAPI()
