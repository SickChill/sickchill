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

import abc
import sickbeard


class Indexer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        self.name = 'Generic'
        self.trakt_id = 'generic'

        self.language = sickbeard.INDEXER_DEFAULT_LANGUAGE
        self.indexer = sickbeard.INDEXER_DEFAULT
        self.timeout = sickbeard.INDEXER_TIMEOUT

    @abc.abstractmethod
    def search(self, text, language=None):
        pass

    @abc.abstractmethod
    def get_show_by_id(self, indexerid, language=None, indexer=None):
        pass

    @abc.abstractmethod
    def get_show_by_name(self, indexerid, language=None, indexer=None):
        pass

    @abc.abstractmethod
    def series_title(self, show):
        pass

    @abc.abstractmethod
    def seasons(self, show):
        pass

    @abc.abstractmethod
    def episodes(self, show, season):
        pass

    @abc.abstractproperty
    def languages(self):
        pass
