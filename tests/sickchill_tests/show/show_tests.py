# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
# Git: https://github.com/SickChill/SickChill.git
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

"""
Test shows
"""


from __future__ import print_function, unicode_literals

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard
import six

from sickbeard.common import Quality
from sickbeard.tv import TVShow
from sickchill.helper.exceptions import MultipleShowObjectsException
from sickchill.show.Show import Show


class ShowTests(unittest.TestCase):
    """
    Test shows
    """

    def test_find(self):
        """
        Test find tv shows by indexer_id
        """
        sickbeard.QUALITY_DEFAULT = Quality.FULLHDTV

        sickbeard.showList = []

        show123 = TestTVShow(0, 123)
        show456 = TestTVShow(0, 456)
        show789 = TestTVShow(0, 789)
        shows = [show123, show456, show789]
        shows_duplicate = shows + shows

        test_cases = {
            (False, None): None,
            (False, ''): None,
            (False, '123'): None,
            (False, 123): None,
            (False, 12.3): None,
            (True, None): None,
            (True, ''): None,
            (True, '123'): None,
            (True, 123): show123,
            (True, 12.3): None,
            (True, 456): show456,
            (True, 789): show789,
        }

        unicode_test_cases = {
            (False, ''): None,
            (False, '123'): None,
            (True, ''): None,
            (True, '123'): None,
        }

        for tests in test_cases, unicode_test_cases:
            for ((use_shows, indexer_id), result) in six.iteritems(tests):
                if use_shows:
                    self.assertEqual(Show.find(shows, indexer_id), result)
                else:
                    self.assertEqual(Show.find(None, indexer_id), result)

        with self.assertRaises(MultipleShowObjectsException):
            Show.find(shows_duplicate, 456)

    def test_validate_indexer_id(self):
        """
        Tests if the indexer_id is valid and if so if it returns the right show
        """
        sickbeard.QUALITY_DEFAULT = Quality.FULLHDTV

        sickbeard.showList = []

        show123 = TestTVShow(0, 123)
        show456 = TestTVShow(0, 456)
        show789 = TestTVShow(0, 789)
        sickbeard.showList = [
            show123,
            show456,
            show789,
        ]

        invalid_show_id = ('Invalid show ID', None)

        indexer_id_list = [
            None, '', '', '123', '123', '456', '456', '789', '789', 123, 456, 789, ['123', '456'], ['123', '456'],
            [123, 456]
        ]
        results_list = [
            invalid_show_id, invalid_show_id, invalid_show_id, (None, show123), (None, show123), (None, show456),
            (None, show456), (None, show789), (None, show789), (None, show123), (None, show456), (None, show789),
            invalid_show_id, invalid_show_id, invalid_show_id
        ]

        self.assertEqual(
            len(indexer_id_list), len(results_list),
            'Number of parameters ({0:d}) and results ({1:d}) does not match'.format(len(indexer_id_list), len(results_list))
        )

        for (index, indexer_id) in enumerate(indexer_id_list):
            self.assertEqual(Show._validate_indexer_id(indexer_id), results_list[index])


class TestTVShow(TVShow):
    """
    A test `TVShow` object that does not need DB access.
    """

    def __init__(self, indexer, indexer_id):
        super(TestTVShow, self).__init__(indexer, indexer_id)

    def loadFromDB(self):
        """
        Override TVShow.loadFromDB to avoid DB access during testing
        """
        pass


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ShowTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
