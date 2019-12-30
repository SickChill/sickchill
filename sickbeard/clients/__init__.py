# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
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

from collections import OrderedDict

_clients = [
    'utorrent',
    'transmission',
    'deluge',
    'deluged',
    'download_station',
    'rtorrent',
    'rtorrent9',
    'qbittorrent',
    'new_qbittorrent',
    'mlnet',
    'putio'
]

_clients.sort()

default_host = {
    'utorrent': 'http://localhost:8000',
    'transmission': 'http://localhost:9091',
    'deluge': 'http://localhost:8112',
    'deluged': 'scgi://localhost:58846',
    'download_station': 'http://localhost:5000',
    'rtorrent': 'scgi://localhost:5000',
    'rtorrent9': 'scgi://localhost:5000',
    'qbittorrent': 'http://localhost:8080',
    'new_qbittorrent': 'http://localhost:8080',
    'mlnet': 'http://localhost:4080',
    'putio': 'https://api.put.io/login'
}


def getClientInstance(name):
    return __import__('sickbeard.clients.' + name.lower(), fromlist=_clients).Client


def getClientListDict(keys_only=False):
    if keys_only:
        return _clients + ['blackhole']

    result = OrderedDict()
    result['blackhole'] = 'Black Hole'
    for client in _clients:
        result[client] = getClientInstance(client)().name
    return result
