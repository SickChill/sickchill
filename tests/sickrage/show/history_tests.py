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
            'wrong': [],
            'downloaded': Quality.DOWNLOADED,
            'Downloaded': Quality.DOWNLOADED,
            'snatched': Quality.SNATCHED,
            'Snatched': Quality.SNATCHED,
        }

        for (action, result) in tests.iteritems():
            self.assertEqual(History._get_actions(action), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(History)
    TextTestRunner(verbosity=2).run(suite)
