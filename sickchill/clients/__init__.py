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

clients = RegistrableExtensionManager('sickbeard.clients', [
    'deluge = sickbeard.clients.deluge:Client',
    'deluged = sickbeard.clients.deluged:Client',
    'download_station = sickbeard.clients.download_station:Client',
    'mlnet = sickbeard.clients.mlnet:Client',
    'qbittorrent = sickbeard.clients.qbittorrent:Client',
    'new_qbittorrent = sickbeard.clients.new_qbittorrent:Client',
    'putio = sickbeard.clients.putio:Client',
    'rtorrent = sickbeard.clients.rtorrent:Client',
    'rtorrent9 = sickbeard.clients.rtorrent9:Client',
    'transmission = sickbeard.clients.transmission:Client',
    'utorrent = sickbeard.clients.utorrent:Client',
])
