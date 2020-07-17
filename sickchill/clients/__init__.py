# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

# Third Party Imports
from subliminal.extensions import RegistrableExtensionManager

manager = RegistrableExtensionManager('sickchill.clients', [
    'deluge = sickchill.clients.deluge:Client',
    'deluged = sickchill.clients.deluged:Client',
    'download_station = sickchill.clients.download_station:Client',
    'mlnet = sickchill.clients.mlnet:Client',
    'qbittorrent = sickchill.clients.qbittorrent:Client',
    'new_qbittorrent = sickchill.clients.new_qbittorrent:Client',
    'putio = sickchill.clients.putio:Client',
    'rtorrent = sickchill.clients.rtorrent:Client',
    'rtorrent9 = sickchill.clients.rtorrent9:Client',
    'transmission = sickchill.clients.transmission:Client',
    'utorrent = sickchill.clients.utorrent:Client',
])

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
