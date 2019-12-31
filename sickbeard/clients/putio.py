# coding=utf-8

# Author: Clinton Collins <clinton.collins@gmail.com>
# Medicine: Dustyn Gibson <miigotu@gmail.com>
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill.  If not, see <http://www.gnu.org/licenses/>.

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Third Party Imports
from putiopy import Client as PutioClient, ClientError

# First Party Imports
from sickbeard import helpers
from sickbeard.clients.generic import GenericClient


class Client(GenericClient):
    def __init__(self, host=None, username=None, password=None):

        super(Client, self).__init__('put.io', host, username, password)
        self.url = 'https://api.put.io/login'

    def _get_auth(self):
        client = PutioClient(self.password)
        try:
            client.Account.info()
        except ClientError as error:
            helpers.handle_requests_exception(error)
            self.auth = None
        else:
            self.auth = client

        return self.auth

    @property
    def _parent_id(self):
        parent_id = 0
        if self.username is not None and self.username != '':
            for f in self.auth.File.list():
                if f.name == self.username:
                    parent_id = f.id
                    break

        return parent_id

    def _add_torrent_uri(self, result):
        transfer = self.auth.Transfer.add_url(result.url, self._parent_id)

        return transfer.id is not None

    def _add_torrent_file(self, result):
        filename = result.name + '.torrent'
        transfer = self.auth.Transfer.add_torrent(filename, self._parent_id)

        return transfer.id is not None
