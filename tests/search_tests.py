#!/usr/bin/env python2.7
# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import sys, os.path
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import random
import unittest

import test_lib as test

import sickbeard.search as search
import sickbeard
from sickbeard.tv import TVEpisode, TVShow
import sickbeard.common as c

from sickbeard.providers.generic import GenericProvider

tests = {"Game of Thrones":
               {"tvdbid": 121361, "s": 5, "e": [10],
                "s_strings": [{"Season": [u"Game of Thrones S05"]}],
                "e_strings": [{"Episode": [u"Game of Thrones S05E10"]}]}}

class SearchTest(test.SickbeardTestDBCase):

    def __init__(self, something):
        super(SearchTest, self).__init__(something)


def test_generator(curData, name, provider, forceSearch):

    def test(self):
        show = TVShow(1, int(curData["tvdbid"]))
        show.name = name
        show.quality = c.ANY | c.Quality.UNKNOWN | c.Quality.RAWHDTV
        show.saveToDB()
        sickbeard.showList.append(show)

        for epNumber in curData["e"]:
            episode = TVEpisode(show, curData["s"], epNumber)
            episode.status = c.WANTED

            # We arent updating scene numbers, so fake it here
            episode.scene_season = curData["s"]
            episode.scene_episode = epNumber

            episode.saveToDB()

            provider.show = show
            season_strings = provider._get_season_search_strings(episode)
            episode_strings = provider._get_episode_search_strings(episode)

            fail = False
            for cur_string in season_strings, episode_strings:
                if not all([isinstance(cur_string, list), isinstance(cur_string[0], dict)]):
                    print " %s is using a wrong string format!" % provider.name
                    print cur_string
                    fail = True
                    continue

            if fail:
                continue

            try:
                assert(season_strings == curData["s_strings"])
                assert(episode_strings == curData["e_strings"])
            except AssertionError:
                print " %s is using a wrong string format!" % provider.name
                print cur_string
                continue

            search_strings = episode_strings[0]
            #search_strings.update(season_strings[0])
            #search_strings.update({"RSS":['']})

            #print search_strings

            if not provider.public:
                continue

            items = provider._doSearch(search_strings)
            if not items:
                print "No results from provider?"
                continue

            title, url = provider._get_title_and_url(items[0])
            for word in show.name.split(" "):
                if not word in title:
                    print "Show name not in title: %s" % title
                    continue

            if not url:
                print "url is empty"
                continue

            quality = provider.getQuality(items[0])
            size = provider._get_size(items[0])
            if not show.quality & quality:
                print "Quality not in common.ANY, %r" % quality
                continue

    return test

if __name__ == '__main__':
    print "=================="
    print "STARTING - Search TESTS"
    print "=================="
    print "######################################################################"
    # create the test methods
    for forceSearch in (True, False):
        for name, curData in tests.items():
            fname = name.replace(' ', '_')

            for provider in sickbeard.providers.sortedProviderList():
                if provider.providerType == GenericProvider.TORRENT:
                    if forceSearch:
                        test_name = 'test_manual_%s_%s_%s' % (fname, curData["tvdbid"], provider.name)
                    else:
                        test_name = 'test_%s_%s_%s' % (fname, curData["tvdbid"], provider.name)
                    test = test_generator(curData, name, provider, forceSearch)
                    setattr(SearchTest, test_name, test)

    suite = unittest.TestLoader().loadTestsFromTestCase(SearchTest)
    unittest.TextTestRunner(verbosity=2).run(suite)
