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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import abc

# First Party Imports
import sickbeard


class Indexer(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self):
        self.name = 'Generic'
        self.slug = 'generic'

        self.language = sickbeard.INDEXER_DEFAULT_LANGUAGE
        self.indexer = sickbeard.INDEXER_DEFAULT
        self.timeout = sickbeard.INDEXER_TIMEOUT

    @abc.abstractmethod
    def search(self, name, language=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_show_by_id(self, indexerid, language=None):
        raise NotImplementedError

    @abc.abstractmethod
    def get_show_by_name(self, indexerid, language=None):
        raise NotImplementedError

    @abc.abstractmethod
    def episodes(self, show, season):
        raise NotImplementedError

    @abc.abstractmethod
    def episode(self, show, season, episode):
        raise NotImplementedError

    @abc.abstractproperty
    def languages(self):
        raise NotImplementedError

    @abc.abstractproperty
    def lang_dict(self):
        raise NotImplementedError
