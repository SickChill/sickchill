"""Unittests for tvdb_api
"""
import unittest
import test_lib as test

import sys, os.path
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

print sys.path

from sickbeard import show_name_helpers, scene_exceptions, common, name_cache

import sickbeard
from sickbeard import db
from sickbeard.databases import cache_db
from sickbeard.tv import TVShow as Show

from lib.tvdb_api.tvdb_api import *
#import tvdb_api as tvdb_api
import tvdb_api



# class test_tvdb_basic(test.SickbeardTestDBCase):
#     # Used to store the cached instance of Tvdb()
#     t = None
#     
#     def setUp(self):
#         if self.t is None:
#             self.__class__.t = Tvdb(cache = True, banners = False)
#      
#     def test_different_case(self):
#         """Checks the auto-correction of show names is working.
#         It should correct the weirdly capitalised 'sCruBs' to 'Scrubs'
#         """
#         self.assertEquals(self.t['scrubs'][1][4]['episodename'], 'My Old Lady')
#         self.assertEquals(self.t['sCruBs']['seriesname'], 'Scrubs')
# 
#     def test_spaces(self):
#         """Checks shownames with spaces
#         """
#         self.assertEquals(self.t['My Name Is Earl']['seriesname'], 'My Name Is Earl')
#         self.assertEquals(self.t['My Name Is Earl'][1][4]['episodename'], 'Faked His Own Death')
# 
#     def test_numeric(self):
#         """Checks numeric show names
#         """
#         self.assertEquals(self.t['24'][2][20]['episodename'], 'Day 2: 3:00 A.M.-4:00 A.M.')
#         self.assertEquals(self.t['24']['seriesname'], '24')
# 
#     def test_show_iter(self):
#         """Iterating over a show returns each seasons
#         """
#         self.assertEquals(
#             len(
#                 [season for season in self.t['Life on Mars']]
#             ),
#             2
#         )
#     
#     def test_season_iter(self):
#         """Iterating over a show returns episodes
#         """
#         self.assertEquals(
#             len(
#                 [episode for episode in self.t['Life on Mars'][1]]
#             ),
#             8
#         )
# 
#     def test_get_episode_overview(self):
#         """Checks episode overview is retrieved correctly.
#         """
#         self.assertEquals(
#             self.t['Battlestar Galactica (2003)'][1][6]['overview'].startswith(
#                 'When a new copy of Doral, a Cylon who had been previously'),
#             True
#         )
# 
#     def test_get_parent(self):
#         """Check accessing series from episode instance
#         """
#         show = self.t['Battlestar Galactica (2003)']
#         season = show[1]
#         episode = show[1][1]
# 
#         self.assertEquals(
#             season.show,
#             show
#         )
# 
#         self.assertEquals(
#             episode.season,
#             season
#         )
# 
#         self.assertEquals(
#             episode.season.show,
#             show
#         )
# 
#     def test_no_season(self):
#         show = self.t['Katekyo Hitman Reborn']
#         print tvdb_api
#         print show[1][1]


class searchTvdbImdbid(test.SickbeardTestDBCase):
    # Used to store the cached instance of Tvdb()
    t = None

    def setUp(self):
        if self.t is None:
            self.__class__.t = Tvdb(cache = True, useZip = True)

    def test_search(self):
        """Test Tvdb.search method
        """
        results = self.t.search("",imdbid='tt0903747')
        all_ids = results['seriesid']
        self.assertTrue('81189' in all_ids)


class test_tvdb_show_search(test.SickbeardTestDBCase):
    # Used to store the cached instance of Tvdb()
    t = None

    def setUp(self):
        if self.t is None:
            self.__class__.t = Tvdb(cache = True, useZip = True)

    def test_search(self):
        """Test Tvdb.search method
        """
        results = self.t.search("my name is earl")
        all_ids = results['seriesid']
        self.assertTrue('75397' in all_ids)


if __name__ == '__main__':
    print "=================="
    print "STARTING - PostProcessor TESTS"
    print "=================="
    print "######################################################################"
    print "###Test Search Tvdb for show breaking bad, using the imdb id"
    suite = unittest.TestLoader().loadTestsFromTestCase(searchTvdbImdbid)
    unittest.TextTestRunner(verbosity=2).run(suite)
    print "######################################################################"
    print "###Test Search Tvdb for show my name is earl, using the show name"
    suite = unittest.TestLoader().loadTestsFromTestCase(test_tvdb_show_search)
    unittest.TextTestRunner(verbosity=2).run(suite)
