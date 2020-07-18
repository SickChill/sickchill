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
# First Party Imports
import sickbeard
from sickbeard import logger
from sickbeard.classes import NZBSearchResult
from sickchill.helper.common import try_int

# Local Folder Imports
from ..GenericProvider import GenericProvider


class NZBProvider(GenericProvider):
    def __init__(self, name: str, extra_options: tuple = tuple()):
        super().__init__(name, extra_options=tuple(['retention']) + extra_options)

        self.provider_type: str = GenericProvider.NZB
        self.__torznab: bool = False

    @property
    def is_active(self) -> bool:
        return self.config('enabled') and self.config('enabled')

    def _get_result(self, episodes) -> NZBSearchResult:
        result = NZBSearchResult(episodes)
        if self.__torznab or result.url.startswith('magnet'):
            result.resultType = GenericProvider.TORRENT

        return result

    def _get_size(self, item) -> int:
        try:
            size = item.get('links')[1].get('length', -1)
        except (AttributeError, IndexError, TypeError):
            size = -1

        if not size:
            logger.debug('The size was not found in the provider response')

        return try_int(size, -1)

    def _get_storage_dir(self) -> str:
        return sickbeard.NZB_DIR
