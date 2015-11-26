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

import sickbeard

from sickbeard.event_queue import Events
from sickrage.system.Restart import Restart
from unittest import TestCase, TestLoader, TextTestRunner


class RestartTests(TestCase):
    def test_restart(self):
        sickbeard.PID = 123456
        sickbeard.events = Events(None)

        tests = {
            0: False,
            '0': False,
            u'0': False,
            123: False,
            '123': False,
            u'123': False,
            123456: True,
            '123456': True,
            u'123456': True,
        }

        for (pid, result) in tests.iteritems():
            self.assertEqual(Restart.restart(pid), result)


if __name__ == '__main__':
    print('=====> Testing %s' % __file__)

    suite = TestLoader().loadTestsFromTestCase(RestartTests)
    TextTestRunner(verbosity=2).run(suite)
