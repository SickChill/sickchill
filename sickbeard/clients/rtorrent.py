# coding=utf-8
# Author: jkaberg <joel.kaberg@gmail.com>
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


# pylint: disable=line-too-long

# based on fuzemans work
# https://github.com/RuudBurger/CouchPotatoServer/blob/develop/couchpotato/core/downloaders/rtorrent/main.py

from __future__ import absolute_import, print_function, unicode_literals

from lib.rtorrent import RTorrent  # pylint: disable=import-error

import sickbeard
from sickbeard import ex, logger
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):  # pylint: disable=invalid-name
    def __init__(self, host=None, username=None, password=None):
        super(Client, self).__init__('rTorrent', host, username, password)

    def _get_auth(self):
        self.auth = None

        if self.auth is not None:
            return self.auth

        if not self.host:
            return

        tp_kwargs = {}
        if sickbeard.TORRENT_AUTH_TYPE != 'none':
            tp_kwargs['authtype'] = sickbeard.TORRENT_AUTH_TYPE

        if not sickbeard.TORRENT_VERIFY_CERT:
            tp_kwargs['check_ssl_cert'] = False

        if self.username and self.password:
            self.auth = RTorrent(self.host, self.username, self.password, True, tp_kwargs=tp_kwargs)
        else:
            self.auth = RTorrent(self.host, None, None, True)

        return self.auth

    def _add_torrent_uri(self, result):

        if not self.auth:
            return False

        if not result:
            return False

        try:
            # Send magnet to rTorrent
            torrent = self.auth.load_magnet(result.url, result.hash)

            if not torrent:
                return False

            # Set label
            label = sickbeard.TORRENT_LABEL
            if result.show.is_anime:
                label = sickbeard.TORRENT_LABEL_ANIME
            if label:
                torrent.set_custom(1, label)

            if sickbeard.TORRENT_PATH:
                torrent.set_directory(sickbeard.TORRENT_PATH)

            if not sickbeard.TORRENT_PAUSED:
                # Start torrent
                torrent.start()

            return True

        except Exception as error:  # pylint: disable=broad-except
            logger.log('Error while sending torrent: {error}'.format  # pylint: disable=no-member
                       (error=ex(error)), logger.WARNING)
            return False

    def _add_torrent_file(self, result):

        if not self.auth:
            return False

        if not result:
            return False

            # group_name = 'sb_test'.lower() ##### Use provider instead of _test
            # if not self._set_torrent_ratio(group_name):
            # return False

        # Send request to rTorrent
        try:
            # Send torrent to rTorrent
            torrent = self.auth.load_torrent(result.content)

            if not torrent:
                return False

            # Set label
            label = sickbeard.TORRENT_LABEL
            if result.show.is_anime:
                label = sickbeard.TORRENT_LABEL_ANIME
            if label:
                torrent.set_custom(1, label)

            if sickbeard.TORRENT_PATH:
                torrent.set_directory(sickbeard.TORRENT_PATH)

            # Set Ratio Group
            # torrent.set_visible(group_name)

            if not sickbeard.TORRENT_PAUSED:
                # Start torrent
                torrent.start()

            return True

        except Exception as error:  # pylint: disable=broad-except
            logger.log('Error while sending torrent: {error}'.format  # pylint: disable=no-member
                       (error=ex(error)), logger.WARNING)
            return False

    def _set_torrent_ratio(self, name):

        # if not name:
        # return False
        #
        # if not self.auth:
        # return False
        #
        # views = self.auth.get_views()
        #
        # if name not in views:
        # self.auth.create_group(name)

        # group = self.auth.get_group(name)

        # ratio = int(float(sickbeard.TORRENT_RATIO) * 100)
        #
        # try:
        # if ratio > 0:
        #
        # # Explicitly set all group options to ensure it is setup correctly
        # group.set_upload('1M')
        # group.set_min(ratio)
        # group.set_max(ratio)
        # group.set_command('d.stop')
        # group.enable()
        # else:
        # # Reset group action and disable it
        # group.set_command()
        # group.disable()
        #
        # except:
        # return False

        _ = name

        return True

    def testAuthentication(self):
        try:
            self._get_auth()

            if self.auth is not None:
                return True, 'Success: Connected and Authenticated'
            else:
                return False, 'Error: Unable to get {name} Authentication, check your config!'.format(name=self.name)
        except Exception:  # pylint: disable=broad-except
            return False, 'Error: Unable to connect to {name}'.format(name=self.name)
