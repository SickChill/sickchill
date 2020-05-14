# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

# Stdlib Imports
import time
from base64 import b64encode

# Third Party Imports
from deluge_client import DelugeRPCClient, FailedToReconnectException
from requests.compat import urlparse

# First Party Imports
import sickbeard
from sickbeard import logger
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('DelugeD', host, username, password)
        self.client = None

    def setup(self):
        if self.host.startswith('scgi://'):
            self.host = self.host[7:]

        if not self.host.startswith('http'):
            self.host = 'http://{}'.format(self.host)

        parsed_url = urlparse(self.host)
        if self.client and all(
            [
                self.client.host == parsed_url.hostname,
                self.client.port == parsed_url.port,
                self.client.username == self.username,
                self.client.password == self.password
            ]
        ):
            return

        self.client = DelugeRPCClient(parsed_url.hostname, parsed_url.port or 58846, self.username, self.password)

    def _get_auth(self):
        self.setup()
        if not self.client.connected:
            for attempt in range(0, 5):
                try:
                    self.client.connect()
                    break
                except FailedToReconnectException:
                    time.sleep(5)

        self.auth = self.client.connected
        return self.auth

    def _add_torrent_uri(self, result):
        self._get_auth()
        remote_torrent = self.client.core.add_torrent_magnet(result.url, self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _add_torrent_file(self, result):
        self._get_auth()
        if not result.content:
            result.content = {}
            return None

        remote_torrent = self.client.core.add_torrent_file(result.name + '.torrent', b64encode(result.content), self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):
        self._get_auth()
        # No option for this built into the rpc, because it is a plugin
        label = sickbeard.TORRENT_LABEL.lower()
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME.lower()
        if ' ' in label:
            logger.log(self.name + ': Invalid label. Label must not contain a space', logger.ERROR)
            return False

        if label:
            return self.client.core.set_torrent_label(result.hash, label)
        return True

    @staticmethod
    def make_options(result):
        # https://github.com/deluge-torrent/deluge/blob/develop/deluge/core/torrent.py#L130
        options = {}

        if sickbeard.TORRENT_DELUGE_DOWNLOAD_DIR:
            options.update({'download_location': sickbeard.TORRENT_DELUGE_DOWNLOAD_DIR})

        if sickbeard.TORRENT_DELUGE_COMPLETE_DIR:
            options.update({'move_completed': True,
                            'move_completed_path': sickbeard.TORRENT_DELUGE_COMPLETE_DIR
            })

        if sickbeard.TORRENT_PAUSED:
            options.update({'add_paused': True})

        if result.priority == 1:
            # file_priorities (list of int): The priority for files in torrent, range is [0..7] however
            # only [0, 1, 4, 7] are normally used and correspond to [Skip, Low, Normal, High]
            options.update({'file_priorities': 7})

        if result.ratio:
            options.update({'stop_at_ratio': True})
            options.update({'stop_ratio': float(result.ratio)})
            # options.update({'remove_at_ratio': True})
            # options.update({'remove_ratio': float(result.ratio)})

        return options

    def testAuthentication(self):
        if self._get_auth() and self.client.daemon.info():
            return True, 'Success: Connected and Authenticated'
        else:
            return False, 'Error: Unable to Authenticate!  Please check your config!'
