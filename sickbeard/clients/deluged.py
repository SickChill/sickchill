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

# Local Folder Imports
from .__deluge_base import DelugeBase


class Client(GenericClient, DelugeBase):
    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('DelugeD', host, username, password)
        self.client = None

    def setup(self):
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
        remote_torrent = self.client.core.add_torrent_magnet(result.url, self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _add_torrent_file(self, result):
        if not result.content:
            result.content = {}
            return None

        remote_torrent = self.client.core.add_torrent_file(result.name + '.torrent', b64encode(result.content), self.make_options(result))
        if not remote_torrent:
            return None

        result.hash = remote_torrent

        return remote_torrent

    def _set_torrent_label(self, result):
        # No option for this built into the rpc, because it is a plugin
        label = sickbeard.TORRENT_LABEL.lower()
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME.lower()
        if ' ' in label:
            logger.log(self.name + ': Invalid label. Label must not contain a space', logger.ERROR)
            return False

        if label:
            try:
                labels = self.client.label.get_labels()
                if label not in labels:
                    logger.log(self.name + ': ' + label + " label does not exist in Deluge we must add it", logger.DEBUG)
                    self.client.labels.add(label)
                    logger.log(self.name + ': ' + label + " label added to Deluge", logger.DEBUG)

                self.client.label.set_torrent(result.hash, label)
            except:
                logger.log(self.name + ': ' + "label plugin not detected", logger.DEBUG)
                return False

        logger.log(self.name + ': ' + label + " label added to torrent", logger.DEBUG)
        return True

    def testAuthentication(self):
        if self._get_auth() and self.client.daemon.info():
            return True, 'Success: Connected and Authenticated'
        else:
            return False, 'Error: Unable to Authenticate!  Please check your config!'
