# coding=utf-8

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

import re
import json
from base64 import b64encode

import sickbeard
from sickbeard.clients.generic import GenericClient


class TransmissionAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(TransmissionAPI, self).__init__('Transmission', host, username, password)

        if not self.host.endswith('/'):
            self.host += '/'

        if self.rpcurl.startswith('/'):
            self.rpcurl = self.rpcurl[1:]

        if self.rpcurl.endswith('/'):
            self.rpcurl = self.rpcurl[:-1]

        self.url = self.host + self.rpcurl + '/rpc'

    def _get_auth(self):

        post_data = json.dumps({'method': 'session-get', })

        try:
            self.response = self.session.post(self.url, data=post_data.encode('utf-8'), timeout=120,
                                              verify=sickbeard.TORRENT_VERIFY_CERT)
            self.auth = re.search(r'X-Transmission-Session-Id:\s*(\w+)', self.response.text).group(1)
        except Exception:
            return None

        self.session.headers.update({'x-transmission-session-id': self.auth})

        # Validating Transmission authorization
        post_data = json.dumps({'arguments': {},
                                'method': 'session-get'})

        self._request(method='post', data=post_data)

        return self.auth

    def _add_torrent_uri(self, result):

        arguments = {'filename': result.url,
                     'paused': 1 if sickbeard.TORRENT_PAUSED else 0,
                     'download-dir': sickbeard.TORRENT_PATH}

        post_data = json.dumps({'arguments': arguments,
                                'method': 'torrent-add'})

        self._request(method='post', data=post_data)

        return self.response.json()['result'] == "success"

    def _add_torrent_file(self, result):

        arguments = {'metainfo': b64encode(result.content),
                     'paused': 1 if sickbeard.TORRENT_PAUSED else 0,
                     'download-dir': sickbeard.TORRENT_PATH}

        post_data = json.dumps({'arguments': arguments,
                                'method': 'torrent-add'})

        self._request(method='post', data=post_data)

        return self.response.json()['result'] == "success"

    def _set_torrent_ratio(self, result):

        ratio = None
        if result.ratio:
            ratio = result.ratio

        mode = 0
        if ratio:
            if float(ratio) == -1:
                ratio = 0
                mode = 2
            elif float(ratio) >= 0:
                ratio = float(ratio)
                mode = 1  # Stop seeding at seedRatioLimit

        arguments = {'ids': [result.hash],
                     'seedRatioLimit': ratio,
                     'seedRatioMode': mode}

        post_data = json.dumps({'arguments': arguments,
                                'method': 'torrent-set'})

        self._request(method='post', data=post_data)

        return self.response.json()['result'] == "success"

    def _set_torrent_seed_time(self, result):

        if sickbeard.TORRENT_SEED_TIME and sickbeard.TORRENT_SEED_TIME != -1:
            time = int(60 * float(sickbeard.TORRENT_SEED_TIME))
            arguments = {'ids': [result.hash],
                         'seedIdleLimit': time,
                         'seedIdleMode': 1}

            post_data = json.dumps({'arguments': arguments,
                                    'method': 'torrent-set'})

            self._request(method='post', data=post_data)

            return self.response.json()['result'] == "success"
        else:
            return True

    def _set_torrent_priority(self, result):

        arguments = {'ids': [result.hash]}

        if result.priority == -1:
            arguments['priority-low'] = []
        elif result.priority == 1:
            # set high priority for all files in torrent
            arguments['priority-high'] = []
            # move torrent to the top if the queue
            arguments['queuePosition'] = 0
            if sickbeard.TORRENT_HIGH_BANDWIDTH:
                arguments['bandwidthPriority'] = 1
        else:
            arguments['priority-normal'] = []

        post_data = json.dumps({'arguments': arguments,
                                'method': 'torrent-set'})

        self._request(method='post', data=post_data)

        return self.response.json()['result'] == "success"


api = TransmissionAPI()
