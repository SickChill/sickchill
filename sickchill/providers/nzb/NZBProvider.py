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
from __future__ import absolute_import, print_function, unicode_literals

# First Party Imports
import sickbeard
from sickbeard import logger
from sickbeard.classes import NZBSearchResult
from sickchill.helper.common import try_int
from sickchill.providers.GenericProvider import GenericProvider


class NZBProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.provider_type = GenericProvider.NZB
        self.torznab = False

    @property
    def is_active(self):
        return bool(sickbeard.USE_NZBS) and self.is_enabled

    def _get_result(self, episodes):
        result = NZBSearchResult(episodes)
        if self.torznab or result.url.startswith('magnet'):
            result.resultType = GenericProvider.TORRENT

        return result

    def _get_size(self, item):
        try:
            size = item.get('links')[1].get('length', -1)
        except (AttributeError, IndexError, TypeError):
            size = -1

        if not size:
            logger.log('The size was not found in the provider response', logger.DEBUG)

        return try_int(size, -1)

    def _get_storage_dir(self):
        return sickbeard.NZB_DIR
