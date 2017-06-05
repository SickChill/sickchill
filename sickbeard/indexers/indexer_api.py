# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.github.io
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

from __future__ import unicode_literals

import os

import sickbeard
from indexer_config import indexerConfig, initConfig
from sickrage.helper.common import try_int
from sickrage.helper.encoding import ek


class indexerApi(object):
    def __init__(self, indexerID=None):
        self.indexerID = try_int(indexerID, None)

    def __del__(self):
        pass

    def indexer(self, *args, **kwargs):
        if self.indexerID:
            return indexerConfig[self.indexerID]['module'](*args, **kwargs)

    @property
    def config(self):
        if self.indexerID:
            return indexerConfig[self.indexerID]
        _ = initConfig
        if sickbeard.INDEXER_DEFAULT_LANGUAGE in _:
            del _[_['valid_languages'].index(sickbeard.INDEXER_DEFAULT_LANGUAGE)]
        _['valid_languages'].sort()
        _['valid_languages'].insert(0, sickbeard.INDEXER_DEFAULT_LANGUAGE)
        return _

    @property
    def name(self):
        if self.indexerID:
            return indexerConfig[self.indexerID]['name']

    @property
    def api_params(self):
        if self.indexerID:
            if sickbeard.CACHE_DIR:
                indexerConfig[self.indexerID]['api_params']['cache'] = ek(os.path.join, sickbeard.CACHE_DIR, 'indexers', self.name)
            if sickbeard.PROXY_SETTING and sickbeard.PROXY_INDEXERS:
                indexerConfig[self.indexerID]['api_params']['proxy'] = sickbeard.PROXY_SETTING

            return indexerConfig[self.indexerID]['api_params']

    @property
    def cache(self):
        if sickbeard.CACHE_DIR:
            return self.api_params['cache']

    @property
    def indexers(self):
        return dict((int(x['id']), x['name']) for x in indexerConfig.values())

    @property
    def session(self):
        if self.indexerID:
            return indexerConfig[self.indexerID]['session']
