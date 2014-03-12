# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.
import os

import sickbeard

from indexer_config import *
from lib.tvdb_api.tvdb_api import Tvdb
from lib.tvrage_api.tvrage_api import TVRage

class indexerApi:
    def __new__(self, indexer):
        cls = type(indexer)
        new_type = type(cls.__name__ + '_wrapped', (indexerApi, cls), {})
        return object.__new__(new_type)

    def __init__(self, indexer=None, language=None, *args, **kwargs):
        self.name = indexer
        self.config = INDEXER_CONFIG.copy()

        # wrap the indexer API object and return it back
        if indexer is not None:
            if sickbeard.CACHE_DIR:
                    INDEXER_API_PARMS[indexer]['cache'] = os.path.join(sickbeard.CACHE_DIR, indexer)

            lINDEXER_API_PARMS = INDEXER_API_PARMS[indexer].copy()
            lINDEXER_API_PARMS.update(**kwargs)

            self._wrapped = eval(indexer)(*args, **lINDEXER_API_PARMS)

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)

    def __getitem__(self, attr):
        return self._wrapped.__getitem__(attr)