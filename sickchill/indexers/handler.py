# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

from __future__ import print_function, unicode_literals
import sickbeard


class ShowIndexer(object):
    def __init__(self):
        self.indexers = {}
        if sickbeard.INDEXER_DEFAULT is None:
            sickbeard.INDEXER_DEFAULT = 1

    def name(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].name

    def trakt_id(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].trakt_id

    def search(self, indexer=None, *args, **kwargs):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].search(*args, **kwargs)

    @property
    def languages(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].languages
