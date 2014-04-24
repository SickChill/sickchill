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

import unittest

import sys, os.path
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

from sickbeard import indexerApi
from sickbeard import classes

class APICheck(unittest.TestCase):

    lang = "en"
    search_term = 'american'

    results = {}
    final_results = []

    for indexer in indexerApi().indexers:
        lINDEXER_API_PARMS = indexerApi(indexer).api_params.copy()
        lINDEXER_API_PARMS['language'] = lang
        lINDEXER_API_PARMS['custom_ui'] = classes.AllShowsListUI
        t = indexerApi(indexer).indexer(**lINDEXER_API_PARMS)

        print("Searching for Show with searchterm: %s on Indexer: %s" % (search_term, indexerApi(indexer).name))
        try:
            # add search results
            results.setdefault(indexer, []).extend(t[search_term])
        except Exception, e:
            continue


    map(final_results.extend,
        ([[indexerApi(id).name, id, indexerApi(id).config["show_url"], int(show['id']),
           show['seriesname'], show['firstaired']] for show in shows] for id, shows in
         results.items()))


    if __name__ == "__main__":
        unittest.main()