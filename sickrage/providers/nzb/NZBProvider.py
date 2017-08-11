# coding=utf-8
# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

from __future__ import print_function, unicode_literals

import sickbeard
from sickbeard import logger
from sickbeard.classes import NZBSearchResult
from sickrage.helper.common import try_int
from sickrage.providers.GenericProvider import GenericProvider


class NZBProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)

        self.provider_type = GenericProvider.NZB

    def is_active(self):
        return bool(sickbeard.USE_NZBS) and self.is_enabled()

    def _get_result(self, episodes):
        return NZBSearchResult(episodes)

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
