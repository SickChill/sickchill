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
Test shutdown
"""

# Stdlib Imports
import unittest

# First Party Imports
import sickbeard
from sickbeard.event_queue import Events
from sickchill import settings
from sickchill.system.Shutdown import Shutdown


class ShutdownTests(unittest.TestCase):
    """
    Test shutdown
    """
    def test_shutdown(self):
        """
        Test shutdown
        """
        settings.PID = 123456
        settings.events = Events(None)

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
            for (pid, result) in tests.items():
                self.assertEqual(Shutdown.stop(pid), result)


if __name__ == '__main__':
    print('=====> Testing {0}'.format(__file__))

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ShutdownTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
