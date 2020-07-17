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
    "mede8er = sickchill.providers.metadata.mede8er:Mede8erMetadata",
    "ps3 = sickchill.providers.metadata.ps3:PS3Metadata",
    "tivo = sickchill.providers.metadata.tivo:TIVOMetadata",
    "mede8er = sickchill.providers.metadata.mede8er:Mede8erMetadata",
    "tivo = sickchill.providers.metadata.tivo:TIVOMetadata",
    "mediabrowser = sickchill.providers.metadata.mediabrowser:MediaBrowserMetadata",
    "wdtv = sickchill.providers.metadata.wdtv:WDTVMetadata",
    "kodi = sickchill.providers.metadata.kodi:KODIMetadata",
    "wdtv = sickchill.providers.metadata.wdtv:WDTVMetadata",
    "kodi = sickchill.providers.metadata.kodi:KODIMetadata",
    "kodi_12plus = sickchill.providers.metadata.kodi_12plus:KODI_12PlusMetadata",
    "mediabrowser = sickchill.providers.metadata.mediabrowser:MediaBrowserMetadata",
    "ps3 = sickchill.providers.metadata.ps3:PS3Metadata",
    "kodi_12plus = sickchill.providers.metadata.kodi_12plus:KODI_12PlusMetadata",
])
