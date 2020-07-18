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
# Stdlib Imports
from xmlrpc.client import ServerProxy

# Third Party Imports
from rtorrent_xmlrpc import SCGIServerProxy

# First Party Imports
from sickbeard import logger
from sickchill.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self):
        super().__init__('rTorrent v9+', extra_options=('host', 'username', 'password'))

    def _get_auth(self):

        if self.auth:
            return self.auth

        if not self.config('host'):
            return

        # TODO: Add back auth for rtorrent
        # tp_kwargs = {}
        # if self.config('auth_type') and self.config('auth_type') != 'none':
        #     tp_kwargs['authtype'] = self.config('auth_type')
        #
        # tp_kwargs['check_ssl_cert'] = self.config('ssl_verify')

        if self.config('host').startswith('scgi'):
            self.auth = SCGIServerProxy(self.config('host'))
        else:
            self.auth = ServerProxy(self.config('host'))

        # self.auth = SCGIServerProxy(self.config('host'), True, tp_kwargs=tp_kwargs)

        return self.auth

    def _add_torrent_uri(self, result):

        if not (self.auth and result):
            return False

        try:
            # Send torrent magnet with params to rTorrent and optionally start download
            torrent = self.auth.load_magnet(result.url, result.hash, start=not self.config('add_paused'), params=self._get_params(result))

            if not torrent:
                return False

            return True

        except Exception as error:
            logger.warning('Error while sending torrent: {error}'.format
                       (error=str(error)))
            return False

    def _add_torrent_file(self, result):

        if not (self.auth and result):
            return False

        try:

            # Send torrent file with params to rTorrent and optionally start download
            torrent = self.auth.load_torrent(result.content, start=not self.config('add_paused'), params=self._get_params(result))

            if not torrent:
                return False

            return True

        except Exception as error:
            logger.warning('Error while sending torrent: {error}'.format
                       (error=str(error)))
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

        return True

    def testAuthentication(self):
        try:
            self._get_auth()

            if self.auth is not None:
                return True, 'Success: Connected and Authenticated'
            else:
                return False, 'Error: Unable to get {name} Authentication, check your config!'.format(name=self.name)
        except Exception:
            return False, 'Error: Unable to connect to {name}'.format(name=self.name)

    def _get_params(self, result):
        params = []

        # Set label
        label = self.config('label')
        if result.show.is_anime:
            label = self.config('label_anime')
        if label:
            params.append('d.custom1.set={0}'.format(label))

        # Set download folder
        if self.config('download_path'):
            params.append('d.directory.set={0}'.format(self.config('download_path')))

        return params
