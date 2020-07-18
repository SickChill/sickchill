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
# Third Party Imports
from subliminal.extensions import RegistrableExtensionManager

manager = RegistrableExtensionManager('sickchill.providers.metadata', [
    "kodi = sickchill.providers.metadata.kodi:Metadata",
    "mede8er = sickchill.providers.metadata.mede8er:Metadata",
    "mediabrowser = sickchill.providers.metadata.mediabrowser:Metadata",
    "ps3 = sickchill.providers.metadata.ps3:Metadata",
    "tivo = sickchill.providers.metadata.tivo:Metadata",
    "wdtv = sickchill.providers.metadata.wdtv:Metadata",
])


def get_config(provider: str, key: str = ''):
    result = manager[provider].plugin().__config
    if key:
        result = result[key]
    return result


def set_config(provider: str, key: str, value):
    get_config(provider)[key] = value

