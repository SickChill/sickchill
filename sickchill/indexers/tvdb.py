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

from .base import Indexer


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = 'theTVDB'
        self.trakt_id = 'tvdb'

    def get_show_by_id(self, id, language=None, indexer=None):
        pass

    def get_show_by_name(self, indexerid, language=None, indexer=None):
        pass

    def seasons(self, show):
        pass

    def episodes(self, show, season):
        pass

    def search(self, text, language=None):
        pass

    def series_title(self, show):
        pass

    @property
    def languages(self):
        return [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]
