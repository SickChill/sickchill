# coding=utf-8
"""
Test scene helpers
"""


import sys
import unittest

import tests.test_lib as test
import sickbeard
from sickbeard import common, db, name_cache, scene_exceptions, show_name_helpers
from sickbeard.tv import TVShow as Show


class SceneTests(test.SickbeardTestDBCase):
    """
    Test Scene
    """
    def _test_all_possible_show_names(self, name, indexerid=0, expected=None):
        """
        Test all possible show names

        :param name:
        :param indexerid:
        :param expected:
        :return:
        """
        expected = expected or []
        show = Show(1, indexerid)
        show.name = name

        result = show_name_helpers.allPossibleShowNames(show)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

    def test_all_possible_show_names(self):
        """
        Test all possible show names
        """
        # common.sceneExceptions[-1] = ['Exception Test']
        test_cache_db_con = db.DBConnection('cache.db')
        test_cache_db_con.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)", [-1, 'Exception Test', -1])
        common.countryList['Full Country Name'] = 'FCN'

        self._test_all_possible_show_names('Show Name', expected=['Show Name'])
        self._test_all_possible_show_names('Show Name', -1, expected=['Show Name', 'Exception Test'])
        self._test_all_possible_show_names('Show Name FCN', expected=['Show Name FCN', 'Show Name (Full Country Name)'])
        self._test_all_possible_show_names('Show Name (FCN)', expected=['Show Name (FCN)', 'Show Name (Full Country Name)'])
        self._test_all_possible_show_names('Show Name Full Country Name', expected=['Show Name Full Country Name', 'Show Name (FCN)'])
        self._test_all_possible_show_names('Show Name (Full Country Name)', expected=['Show Name (Full Country Name)', 'Show Name (FCN)'])

    def test_filter_bad_releases(self):
        """
        Test filtering of bad releases
        """
        sickbeard.IGNORE_WORDS = 'GermaN'
        sickbeard.REQUIRE_WORDS = 'STUFF'
        self.assertFalse(show_name_helpers.filter_bad_releases('Show.S02.German.Stuff-Grp'))
        self.assertTrue(show_name_helpers.filter_bad_releases('Show.S02.Some.Stuff-Core2HD'))
        self.assertFalse(show_name_helpers.filter_bad_releases('Show.S02.Some.German.Stuff-Grp'))
        # self.assertTrue(show_name_helpers.filter_bad_releases('German.Show.S02.Some.Stuff-Grp'))
        self.assertFalse(show_name_helpers.filter_bad_releases('Show.S02.This.Is.German'))


class SceneExceptionTestCase(test.SickbeardTestDBCase):
    """
    Test scene exceptions test case
    """
    def setUp(self):
        """
        Set up tests
        """
        super(SceneExceptionTestCase, self).setUp()
        scene_exceptions.retrieve_exceptions()

    def test_scene_ex_empty(self):
        """
        Test empty scene exception
        """
        self.assertEqual(scene_exceptions.get_scene_exceptions(0), [])

    def test_scene_ex_babylon_5(self):
        """
        Test scene exceptions for Babylon 5
        """
        self.assertEqual(sorted(scene_exceptions.get_scene_exceptions(70726)), ['Babylon 5', 'Babylon5'])

    def test_scene_ex_by_name(self):
        """
        Test scene exceptions by name
        :return:
        """
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('Babylon5'), (70726, -1))
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('babylon 5'), (70726, -1))
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('Carlos 2010'), (164451, -1))

    def test_scene_ex_by_name_empty(self):
        """
        Test scene exceptions by name are empty
        """
        self.assertEqual(scene_exceptions.get_scene_exception_by_name('nothing useful'), (None, None))

    def test_scene_ex_reset_name_cache(self):
        """
        Test scene exceptions reset name cache
        """
        # clear the exceptions
        test_cache_db_con = db.DBConnection('cache.db')
        test_cache_db_con.action("DELETE FROM scene_exceptions")

        # put something in the cache
        name_cache.addNameToCache('Cached Name', 0)

        # updating should not clear the cache this time since our exceptions didn't change
        scene_exceptions.retrieve_exceptions()
        self.assertEqual(name_cache.retrieveNameFromCache('Cached Name'), 0)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        SUITE = unittest.TestLoader().loadTestsFromName('scene_helpers_tests.SceneExceptionTestCase.test_' + sys.argv[1])
        unittest.TextTestRunner(verbosity=2).run(SUITE)
    else:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(SceneTests)
        unittest.TextTestRunner(verbosity=2).run(SUITE)

        SUITE = unittest.TestLoader().loadTestsFromTestCase(SceneExceptionTestCase)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
