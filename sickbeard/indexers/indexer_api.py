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

#import sickbeard
import generic

from lib.tvdb_api.tvdb_api import Tvdb
from lib.tvrage_api.tvrage_api import TVRage

class indexerApi(generic.GenericIndexer):
    def __init__(self, indexer=None, *args, **kwargs):
        super(indexerApi, self).__init__(indexer)
        self.name = self.config['name']

        if indexer:
            self.config['api_parms'].update(**kwargs)

            #if sickbeard.CACHE_DIR:
            #    self.api_parms['cache'] = os.path.join(sickbeard.CACHE_DIR, indexer)

            # wrap the indexer API object and return it back
            self._wrapped = eval(indexer)(*args, **self.config['api_parms'])

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)

    def __getitem__(self, attr):
        return self._wrapped.__getitem__(attr)