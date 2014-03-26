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

from indexer_config import initConfig, indexerConfig


class indexerApi(object):
    def __init__(self, indexer=None, *args, **kwargs):
        self._wrapped = object
        self.config = initConfig
        self.indexers = {k: v if k is 'id' else v['name'] for k, v in indexerConfig.items()}

        if indexer in indexerConfig:
            self.name = indexerConfig[indexer]['name']
            self.config = indexerConfig[indexer]

            # set cache if exists
            if sickbeard.CACHE_DIR: indexerConfig[indexer]['api_params']['cache'] = os.path.join(sickbeard.CACHE_DIR,
                                                                                                 self.name)
            # update API params
            indexerConfig[indexer]['api_params'].update(**kwargs)

            # wrap the indexer API object and return it back
            self._wrapped = indexerConfig[indexer]['module'](*args, **indexerConfig[indexer]['api_params'])

    def __getattr__(self, attr):
        return getattr(self._wrapped, attr)

    def __getitem__(self, attr):
        return self._wrapped.__getitem__(attr)
