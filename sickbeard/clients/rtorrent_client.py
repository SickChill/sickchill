# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
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

# File based on work done by Medariox and Fuzeman

# pylint: disable=line-too-long

from __future__ import print_function, unicode_literals

from rtorrent import RTorrent  # pylint: disable=import-error

import sickbeard
from sickbeard import ex, logger
from sickbeard.clients.generic import GenericClient


class rTorrentAPI(GenericClient):  # pylint: disable=invalid-name
    def __init__(self, host=None, username=None, password=None):
        super(rTorrentAPI, self).__init__('rTorrent', host, username, password)

    def _get_auth(self):

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

        if not (self.auth and result):
            return False

        try:

            # Send torrent magnet with params to rTorrent and optionally start download
            torrent = self.auth.load_magnet(result.url, result.hash, start=not sickbeard.TORRENT_PAUSED, params=self._get_params(result))

            if not torrent:
                return False

            return True

        except Exception as error:  # pylint: disable=broad-except
            logger.log('Error while sending torrent: {error}'.format  # pylint: disable=no-member
                       (error=ex(error)), logger.WARNING)
            return False

    def _add_torrent_file(self, result):

        if not (self.auth and result):
            return False

        try:

            # Send torrent file with params to rTorrent and optionally start download
            torrent = self.auth.load_torrent(result.content, start=not sickbeard.TORRENT_PAUSED, params=self._get_params(result))

            if not torrent:
                return False

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

    @staticmethod
    def _get_params(result):
        params = []

        # Set label
        label = sickbeard.TORRENT_LABEL
        if result.show.is_anime:
            label = sickbeard.TORRENT_LABEL_ANIME
        if label:
            params.append('d.custom1.set={0}'.format(label))

        # Set download folder
        if sickbeard.TORRENT_PATH:
            params.append('d.directory.set={0}'.format(sickbeard.TORRENT_PATH))

        return params

api = rTorrentAPI()  # pylint: disable=invalid-name
