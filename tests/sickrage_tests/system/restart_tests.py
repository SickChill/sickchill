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
Test restart
"""

from __future__ import print_function, unicode_literals

import os
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import sickbeard
from sickbeard.event_queue import Events
from sickrage.system.Restart import Restart


import six


class RestartTests(unittest.TestCase):
    """
    Test restart
    """
    def test_restart(self):
        """
        Test restart
        """
        sickbeard.PID = 123456
        sickbeard.events = Events(None)

        test_cases = {
            0: False,
            '0': False,
            123: False,
            '123': False,
            123456: True,
            '123456': True,
        }

        unicode_test_cases = {
            '0': False,
            '123': False,
            '123456': True,
        }

        for tests in test_cases, unicode_test_cases:
            for (pid, result) in six.iteritems(tests):
                self.assertEqual(Restart.restart(pid), result)


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(RestartTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
