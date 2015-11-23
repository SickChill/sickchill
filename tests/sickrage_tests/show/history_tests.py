# This file is part of SickRage.
#
# URL: https://sickrage.github.io
# Git: https://github.com/SickRage/SickRage.git
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

import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from sickbeard.common import Quality
from sickrage.show.History import History
from unittest import TestCase, TestLoader, TextTestRunner


class HistoryTests(TestCase):
    def test_get_actions(self):
        tests = {
            None: [],
            '': [],
            u'': [],
            'wrong': [],
            u'wrong': [],
            'downloaded': Quality.DOWNLOADED,
            u'downloaded': Quality.DOWNLOADED,
            'Downloaded': Quality.DOWNLOADED,
            u'Downloaded': Quality.DOWNLOADED,
            'snatched': Quality.SNATCHED,
            u'snatched': Quality.SNATCHED,
            'Snatched': Quality.SNATCHED,
            u'Snatched': Quality.SNATCHED,
        }

        for (action, result) in tests.iteritems():
            self.assertEqual(History._get_actions(action), result)

    def test_get_limit(self):
        tests = {
            None: 0,
            '': 0,
            u'': 0,
            '0': 0,
            u'0': 0,
            '5': 5,
            u'5': 5,
            '-5': 0,
            u'-5': 0,
            '1.5': 0,
            u'1.5': 0,
            '-1.5': 0,
            u'-1.5': 0,
            5: 5,
            -5: 0,
            1.5: 1,
            -1.5: 0,
        }

        for (action, result) in tests.iteritems():
            self.assertEqual(History._get_limit(action), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(HistoryTests)
    TextTestRunner(verbosity=2).run(suite)
