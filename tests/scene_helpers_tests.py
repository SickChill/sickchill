# coding=utf-8
"""
Test scene helpers
"""

# pylint: disable=line-too-long

import os.path
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import show_name_helpers, scene_exceptions, common, name_cache, db
from sickbeard.tv import TVShow as Show
import tests.test_lib as test


class SceneTests(test.SickbeardTestDBCase):
    """
    Test Scene
    """
    def _test_scene_to_norm_show_name(self, name, expected):
        """
        Test scene to normal show names

        :param name:
        :param expected:
        :return:
        """
        result = show_name_helpers.sceneToNormalShowNames(name)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

        dot_result = show_name_helpers.sceneToNormalShowNames(name.replace(' ', '.'))
        dot_expected = [x.replace(' ', '.') for x in expected]
        self.assertTrue(len(set(dot_expected).intersection(set(dot_result))) == len(dot_expected))

    def _test_all_possible_show_names(self, name, indexerid=0, expected=None):
        """
        Test all possible show names

        :param name:
        :param indexerid:
        :param expected:
        :return:
        """
        expected = [] if expected is None else expected
        show = Show(1, indexerid)
        show.name = name

        result = show_name_helpers.allPossibleShowNames(show)
        self.assertTrue(len(set(expected).intersection(set(result))) == len(expected))

    def _test_filter_bad_releases(self, name, expected):
        """
        Test filter of bad releases

        :param name:
        :param expected:
        :return:
        """
        result = show_name_helpers.filterBadReleases(name)
        self.assertEqual(result, expected)

    def _test_is_good_name(self, name, show):
        """
        Test if name is good

        :param name:
        :param show:
        :return:
        """
        self.assertTrue(show_name_helpers.isGoodResult(name, show))

    def test_is_good_name(self):
        """
        Perform good name tests
        """
        list_of_cases = [('Show.Name.S01E02.Test-Test', 'Show/Name'),
                         ('Show.Name.S01E02.Test-Test', 'Show. Name'),
                         ('Show.Name.S01E02.Test-Test', 'Show- Name'),
                         ('Show.Name.Part.IV.Test-Test', 'Show Name'),
                         ('Show.Name.S01.Test-Test', 'Show Name'),
                         ('Show.Name.E02.Test-Test', 'Show: Name'),
                         ('Show Name Season 2 Test', 'Show: Name'), ]

        for test_case in list_of_cases:
            scene_name, show_name = test_case
            show = Show(1, 0)
            show.name = show_name
            self._test_is_good_name(scene_name, show)

    def test_scene_to_norm_show_names(self):
        """
        Test scene to normal show names
        """
        self._test_scene_to_norm_show_name('Show Name 2010', ['Show Name 2010', 'Show Name (2010)'])
        self._test_scene_to_norm_show_name('Show Name US', ['Show Name US', 'Show Name (US)'])
        self._test_scene_to_norm_show_name('Show Name AU', ['Show Name AU', 'Show Name (AU)'])
        self._test_scene_to_norm_show_name('Show Name CA', ['Show Name CA', 'Show Name (CA)'])
        self._test_scene_to_norm_show_name('Show and Name', ['Show and Name', 'Show & Name'])
        self._test_scene_to_norm_show_name('Show and Name 2010', ['Show and Name 2010', 'Show & Name 2010', 'Show and Name (2010)', 'Show & Name (2010)'])
        self._test_scene_to_norm_show_name('show name us', ['show name us', 'show name (us)'])
        self._test_scene_to_norm_show_name('Show And Name', ['Show And Name', 'Show & Name'])

        # failure cases
        self._test_scene_to_norm_show_name('Show Name 90210', ['Show Name 90210'])
        self._test_scene_to_norm_show_name('Show Name YA', ['Show Name YA'])

    def test_all_possible_show_names(self):
        """
        Test all possible show names
        """
        # common.sceneExceptions[-1] = ['Exception Test']
        my_db = db.DBConnection("cache.db")
        my_db.action("INSERT INTO scene_exceptions (indexer_id, show_name, season) VALUES (?,?,?)", [-1, 'Exception Test', -1])
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
        self._test_filter_bad_releases('Show.S02.German.Stuff-Grp', False)
        self._test_filter_bad_releases('Show.S02.Some.Stuff-Core2HD', False)
        self._test_filter_bad_releases('Show.S02.Some.German.Stuff-Grp', False)
        # self._test_filter_bad_releases('German.Show.S02.Some.Stuff-Grp', True)
        self._test_filter_bad_releases('Show.S02.This.Is.German', False)


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
        my_db = db.DBConnection("cache.db")
        my_db.action("DELETE FROM scene_exceptions")

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
