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

import tvdbsimple

from .base import Indexer


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = 'theTVDB'
        self.trakt_id = 'tvdb'
        self.api_key = 'F9C450E78D99172E'
        tvdbsimple.KEYS.API_KEY = self.api_key
        self.search = tvdbsimple.search.Search().series
        self.series = tvdbsimple.series.Series

    def get_show_by_id(self, indexerid, language=None):
        return self.series(indexerid, language)

    def get_show_by_name(self, name, indexerid=None, language=None):
        if indexerid:
            return self.get_show_by_id(indexerid, language)
        # Just return the first result for now
        return self.series(self.search(name, language)[0]['id'])

    def seasons(self, show):
        pass

    def episodes(self, show, season):
        pass

    def search(self, name, language=None):
        return self.search(name, language)

    def series_title(self, show):
        pass

    @property
    def languages(self):
        return [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]
