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
Test history
"""

from __future__ import print_function, unicode_literals

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickbeard.common import Quality
from sickchill.show.History import History


import six


class HistoryTests(unittest.TestCase):
    """
    Test history
    """
    def test_get_actions(self):
        """
        Tests whether or not the different kinds of actions an episode can have are returned correctly
        """
        test_cases = {
            None: [],
            '': [],
            'wrong': [],
            'downloaded': Quality.DOWNLOADED,
            'Downloaded': Quality.DOWNLOADED,
            'snatched': Quality.SNATCHED,
            'Snatched': Quality.SNATCHED,
        }

        unicode_test_cases = {
            '': [],
            'wrong': [],
            'downloaded': Quality.DOWNLOADED,
            'Downloaded': Quality.DOWNLOADED,
            'snatched': Quality.SNATCHED,
            'Snatched': Quality.SNATCHED,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in six.iteritems(tests):
                self.assertEqual(History._get_actions(action), result)

    def test_get_limit(self):
        """
        Tests the static get limit method which should return the limit on the amount of elements that should be shown/returned
        """
        test_cases = {
            None: 0,
            '': 0,
            '0': 0,
            '5': 5,
            '-5': 0,
            '1.5': 0,
            '-1.5': 0,
            5: 5,
            -5: 0,
            1.5: 1,
            -1.5: 0,
        }

        unicode_test_cases = {
            '': 0,
            '0': 0,
            '5': 5,
            '-5': 0,
            '1.5': 0,
            '-1.5': 0,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in six.iteritems(tests):
                self.assertEqual(History._get_limit(action), result)


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
