# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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

__all__ = [
    'utorrent',
    'transmission',
    'deluge',
    'deluged',
    'download_station',
    'rtorrent',
    'qbittorrent',
    'mlnet'
]

default_host = {
    'utorrent': 'http://localhost:8000',
    'transmission': 'http://localhost:9091',
    'deluge': 'http://localhost:8112',
    'deluged': 'scgi://localhost:58846',
    'download_station': 'http://localhost:5000',
    'rtorrent': 'scgi://localhost:5000',
    'qbittorrent': 'http://localhost:8080',
    'mlnet': 'http://localhost:4080'
}


def getClientModule(name):
    name = name.lower()
    prefix = "sickbeard.clients."

    return __import__(prefix + name + '_client', fromlist=__all__)


def getClientIstance(name):
    module = getClientModule(name)
    className = module.api.__class__.__name__

    return getattr(module, className)
