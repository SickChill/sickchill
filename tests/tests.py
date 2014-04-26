# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
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

from __future__ import with_statement
import re

import unittest

import sys, os.path

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import sickbeard
from lib.feedparser import feedparser

class APICheck(unittest.TestCase):
    resultFilters = ["sub(pack|s|bed)", "swesub(bed)?",
                     "(dir|sample|sub|nfo)fix", "sample", "(dvd)?extras",
                     "dub(bed)?"]

    search_term = u'Watershed.-.Exploring.a.New.Water.Ethic.for.the.New.West.1080i.HDTV.DD2.0.H.264-TrollHD'
    #search_term = re.escape(search_term)

    filters = [re.compile('(^|[\W_]|[\s_])%s($|[\W_]|[\s_])' % filter.strip(), re.I) for filter in resultFilters + sickbeard.IGNORE_WORDS.split(',')]
    for regfilter in filters:
        if regfilter.search(search_term):
            print 'bad'

    print 'good'

    if __name__ == "__main__":
        unittest.main()