# coding=utf-8
# This file is part of SickRage.
#
# URL: https://SickRage.GitHub.io
# Git: https://github.com/SickRage/SickRage.git
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

"""
Test history
"""

from __future__ import print_function

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickbeard.common import Quality
from sickrage.show.History import History


class HistoryTests(unittest.TestCase):
    """
    Test history
    """
    def test_get_actions(self):
        """
        Test get actions
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
            u'': [],
            u'wrong': [],
            u'downloaded': Quality.DOWNLOADED,
            u'Downloaded': Quality.DOWNLOADED,
            u'snatched': Quality.SNATCHED,
            u'Snatched': Quality.SNATCHED,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in tests.iteritems():
                self.assertEqual(History._get_actions(action), result)  # pylint: disable=protected-access

    def test_get_limit(self):
        """
        Test get limit
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
            u'': 0,
            u'0': 0,
            u'5': 5,
            u'-5': 0,
            u'1.5': 0,
            u'-1.5': 0,
        }

        for tests in test_cases, unicode_test_cases:
            for (action, result) in tests.iteritems():
                self.assertEqual(History._get_limit(action), result)  # pylint: disable=protected-access


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(HistoryTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
