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

from __future__ import print_function, unicode_literals

import json
from base64 import b64encode

import sickbeard
from sickbeard import logger
from sickbeard.clients.generic import GenericClient


class DelugeAPI(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(DelugeAPI, self).__init__('Deluge', host, username, password)

        self.url = self.host + 'json'
        self.session.headers.update({'Content-Type': 'application/json'})

    def _get_auth(self):

        post_data = json.dumps({"method": "auth.login",
                                "params": [self.password],
                                "id": 1})

        try:
            self.response = self.session.post(self.url, data=post_data.encode('utf-8'), verify=sickbeard.TORRENT_VERIFY_CERT)
        except Exception:
            return None

        self.auth = self.response.json()["result"]

        post_data = json.dumps({"method": "web.connected",
                                "params": [],
                                "id": 10})

        try:
            self.response = self.session.post(self.url, data=post_data.encode('utf-8'), verify=sickbeard.TORRENT_VERIFY_CERT)
        except Exception:
            return None

        connected = self.response.json()['result']

        if not connected:
            post_data = json.dumps({"method": "web.get_hosts",
                                    "params": [],
                                    "id": 11})
            try:
                self.response = self.session.post(self.url, data=post_data.encode('utf-8'), verify=sickbeard.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            hosts = self.response.json()['result']
            if not hosts:
                logger.log(self.name + ': WebUI does not contain daemons', logger.ERROR)
                return None

            post_data = json.dumps({"method": "web.connect",
                                    "params": [hosts[0][0]],
                                    "id": 11})

            try:
                self.response = self.session.post(self.url, data=post_data.encode('utf-8'), verify=sickbeard.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            post_data = json.dumps({"method": "web.connected",
                                    "params": [],
                                    "id": 10})

            try:
                self.response = self.session.post(self.url, data=post_data.encode('utf-8'), verify=sickbeard.TORRENT_VERIFY_CERT)
            except Exception:
                return None

            connected = self.response.json()['result']
            if not connected:
                logger.log(self.name + ': WebUI could not connect to daemon', logger.ERROR)
                return None

        return self.auth

    def _add_torrent_uri(self, result):

        post_data = json.dumps({"method": "core.add_torrent_magnet",
                                "params": [result.url, {}],
                                "id": 2})

        self._request(method='post', data=post_data)

        result.hash = self.response.json()['result']

        return self.response.json()['result']

    def _add_torrent_file(self, result):

        post_data = json.dumps({"method": "core.add_torrent_file",
                                "params": [result.name + '.torrent', b64encode(result.content), {}],
                                "id": 2})

        self._request(method='post', data=post_data)

        result.hash = self.response.json()['result']

        return self.response.json()['result']

    def _set_torrent_label(self, result):

        label = sickbeard.TORRENT_LABEL.lower()
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME.lower()
        if ' ' in label:
            logger.log(self.name + ': Invalid label. Label must not contain a space', logger.ERROR)
            return False

        if label:
            # check if label already exists and create it if not
            post_data = json.dumps({"method": 'label.get_labels',
                                    "params": [],
                                    "id": 3})

            self._request(method='post', data=post_data)
            labels = self.response.json()['result']

            if labels is not None:
                if label not in labels:
                    logger.log(self.name + ': ' + label + " label does not exist in Deluge we must add it",
                               logger.DEBUG)
                    post_data = json.dumps({"method": 'label.add',
                                            "params": [label],
                                            "id": 4})

                    self._request(method='post', data=post_data)
                    logger.log(self.name + ': ' + label + " label added to Deluge", logger.DEBUG)

                # add label to torrent
                post_data = json.dumps({"method": 'label.set_torrent',
                                        "params": [result.hash, label],
                                        "id": 5})

                self._request(method='post', data=post_data)
                logger.log(self.name + ': ' + label + " label added to torrent", logger.DEBUG)
            else:
                logger.log(self.name + ': ' + "label plugin not detected", logger.DEBUG)
                return False

        return not self.response.json()['error']

    def _set_torrent_ratio(self, result):

        ratio = None
        if result.ratio:
            ratio = result.ratio

        if ratio:
            post_data = json.dumps({"method": "core.set_torrent_stop_at_ratio",
                                    "params": [result.hash, True],
                                    "id": 5})

            self._request(method='post', data=post_data)

            post_data = json.dumps({"method": "core.set_torrent_stop_ratio",
                                    "params": [result.hash, float(ratio)],
                                    "id": 6})

            self._request(method='post', data=post_data)

            return not self.response.json()['error']

        return True

    def _set_torrent_path(self, result):

        if sickbeard.TORRENT_PATH:
            post_data = json.dumps({"method": "core.set_torrent_move_completed",
                                    "params": [result.hash, True],
                                    "id": 7})

            self._request(method='post', data=post_data)

            post_data = json.dumps({"method": "core.set_torrent_move_completed_path",
                                    "params": [result.hash, sickbeard.TORRENT_PATH],
                                    "id": 8})

            self._request(method='post', data=post_data)

            return not self.response.json()['error']

        return True

    def _set_torrent_pause(self, result):

        if sickbeard.TORRENT_PAUSED:
            post_data = json.dumps({"method": "core.pause_torrent",
                                    "params": [[result.hash]],
                                    "id": 9})

            self._request(method='post', data=post_data)

            return not self.response.json()['error']

        return True


api = DelugeAPI()
