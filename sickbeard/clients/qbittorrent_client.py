# Author: Mr_Orange <mr_orange@hotmail.it>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import sickbeard
from .generic import GenericClient
from requests.auth import HTTPDigestAuth

class qbittorrentAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(qbittorrentAPI, self).__init__('qbittorrent', host, username, password)

        self.url = self.host
        self.session.auth = HTTPDigestAuth(self.username, self.password);

    def _get_auth(self):

        try:
            self.response = self.session.get(self.host, verify=False)
            self.auth = self.response.content
        except:
            return None

        return self.auth if not self.response.status_code == 404 else None

    def _add_torrent_uri(self, result):

        self.url = self.host+'command/download'
        data = {'urls': result.url}
        return self._request(method='post', data=data)

    def _add_torrent_file(self, result):

        self.url = self.host+'command/upload'
        files = {'torrents': (result.name + '.torrent', result.content)}
        return self._request(method='post', files=files)

    def _set_torrent_priority(self, result):

        self.url = self.host+'command/decreasePrio '
        if result.priority == 1:
            self.url = self.host+'command/increasePrio'

        data = {'hashes': result.hash}
        return self._request(method='post', data=data)

    def _set_torrent_pause(self, result):
        
        self.url = self.host+'command/resume'
        if sickbeard.TORRENT_PAUSED:
            self.url = self.host+'command/pause'

        data = {'hash': result.hash}
        return self._request(method='post', data=data)

api = qbittorrentAPI()
