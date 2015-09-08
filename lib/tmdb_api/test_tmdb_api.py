"""
test.py contains unit tests for tmdbsimple.py

Fill in Global Variables below before running tests.

Created by Celia Oakley on 2013-11-05
"""

import unittest
import sys

from tmdb_api import TMDB

#
# Global Variables (fill in or put in keys.py)
#
TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'

try:
    from keys import *
except ImportError:
    pass

class TVCheck(unittest.TestCase):
    def testTVInfo(self):
        name = u'Game of Thrones'
        tmdb = TMDB(TMDB_API_KEY)
        find = tmdb.Find(121361)
        response = find.info({'external_source': 'tvdb_id'})
        self.assertEqual(response['tv_results'][0]['name'], name)

    def testTVSearch(self):
        id = 1396
        name = 'UFC'
        tmdb = TMDB(TMDB_API_KEY)

        # get TMDB configuration info
        config = tmdb.Configuration()
        response = config.info()
        base_url = response['images']['base_url']
        sizes = response['images']['poster_sizes']

        def size_str_to_int(x):
            return float("inf") if x == 'original' else int(x[1:])
        max_size = max(sizes, key=size_str_to_int)

        # get show ID on TMDB
        search = tmdb.Search()
        response = search.collection({'query': name})
        for result in response['results']:
            id = result['id']

        # get show images
        collection = tmdb.Collections(id)
        response = collection.images()
        rel_path = response['posters'][0]['file_path']
        url = "{0}{1}{2}".format(base_url, max_size, rel_path)
        self.assertTrue(hasattr(response, name))

    def testTVCredits(self):
        id = 1396
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV(id)
        response = tv.credits()
        self.assertTrue(hasattr(tv, 'cast'))

    def testTVExternalIds(self):
        id = 1396
        imdb_id = 'tt0903747'
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV(id)
        response = tv.external_ids()
        self.assertEqual(tv.imdb_id, imdb_id)

    def testTVImages(self):
        id = 1396
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV(id)
        response = tv.images()
        self.assertTrue(hasattr(tv, 'backdrops'))

    def testTVTranslations(self):
        id = 1396
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV(id)
        response = tv.translations()
        self.assertTrue(hasattr(tv, 'translations'))

    def testTVTopRated(self):
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV()
        response = tv.top_rated()
        self.assertTrue(hasattr(tv, 'results'))

    def testTVPopular(self):
        tmdb = TMDB(TMDB_API_KEY)
        tv = tmdb.TV()
        response = tv.popular()
        self.assertTrue(hasattr(tv, 'results'))

class TVSeasonsCheck(unittest.TestCase):
    def testTVSeasonsInfo(self):
        id = 3572
        season_number = 1
        name = 'Season 1'
        tmdb = TMDB(TMDB_API_KEY)
        tv_seasons = tmdb.TV_Seasons(id, season_number)
        response = tv_seasons.info()
        self.assertEqual(tv_seasons.name, name)

    def testTVSeasonsCredits(self):
        id = 3572
        season_number = 1
        tmdb = TMDB(TMDB_API_KEY)
        tv_seasons = tmdb.TV_Seasons(id, season_number)
        response = tv_seasons.credits()
        self.assertTrue(hasattr(tv_seasons, 'crew'))

    def testTVSeasonsExternalIds(self):
        id = 3572
        season_number = 1
        tvdb_id = 2547
        tmdb = TMDB(TMDB_API_KEY)
        tv_seasons = tmdb.TV_Seasons(id, season_number)
        response = tv_seasons.external_ids()
        self.assertEqual(tv_seasons.tvdb_id, tvdb_id)

    def testTVSeasonsImages(self):
        id = 3572
        season_number = 1
        tmdb = TMDB(TMDB_API_KEY)
        tv_seasons = tmdb.TV_Seasons(id, season_number)
        response = tv_seasons.images()
        self.assertTrue(hasattr(tv_seasons, 'posters'))

class TVEpisodesCheck(unittest.TestCase):
    def testTVEpisodesInfo(self):
        id = 1396
        season_number = 1
        episode_number = 1
        name = 'Pilot'
        tmdb = TMDB(TMDB_API_KEY)
        tv_episodes = tmdb.TV_Episodes(id, season_number, episode_number)
        response = tv_episodes.info()
        self.assertEqual(tv_episodes.name, name)

    def testTVEpisodesCredits(self):
        id = 1396
        season_number = 1
        episode_number = 1
        tmdb = TMDB(TMDB_API_KEY)
        tv_episodes = tmdb.TV_Episodes(id, season_number, episode_number)
        response = tv_episodes.credits()
        self.assertTrue(hasattr(tv_episodes, 'guest_stars'))

    def testTVEpisodesExternalIds(self):
        id = 1396
        season_number = 1
        episode_number = 1
        imdb_id = 'tt0959621'
        tmdb = TMDB(TMDB_API_KEY)
        tv_episodes = tmdb.TV_Episodes(id, season_number, episode_number)
        response = tv_episodes.external_ids()
        self.assertEqual(tv_episodes.imdb_id, imdb_id)

    def testTVEpisodesImages(self):
        id = 1396
        season_number = 1
        episode_number = 1
        tmdb = TMDB(TMDB_API_KEY)
        tv_episodes = tmdb.TV_Episodes(id, season_number, episode_number)
        response = tv_episodes.images()
        self.assertTrue(hasattr(tv_episodes, 'stills'))

if __name__ == "__main__":
    unittest.main()

# Run with:
#   python3 test_tmdbsimple.py ConfigurationCheck -v
#   python3 test_tmdbsimple.py ConfigurationCheck
#   ... or other Check classes
#   python3 test_tmdbsimple.py -v
#   python3 test_tmdbsimple.py
