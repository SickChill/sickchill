# coding=utf-8
# Author: The SickRage Dev Team
#
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

from bs4 import BeautifulSoup


class BS4Parser(object):
    def __init__(self, *args, **kwargs):
        self.soup = BeautifulSoup(*args, **kwargs)

    def __enter__(self):
        return self.soup

    def __exit__(self, exc_ty, exc_val, tb):
        _ = exc_ty, exc_val, tb  # Throw away unused values
        self.soup.clear(True)
        self.soup = None
