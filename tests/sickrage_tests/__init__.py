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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

"""
Tests for SickRage
"""

from __future__ import print_function

from tests.sickrage_tests.helper.common_tests import CommonTests
from tests.sickrage_tests.helper.quality_tests import QualityTests
from tests.sickrage_tests.show.coming_episodes_tests import ComingEpisodesTests
from tests.sickrage_tests.show.history_tests import HistoryTests
from tests.sickrage_tests.show.show_tests import ShowTests
from tests.sickrage_tests.system.restart_tests import RestartTests
from tests.sickrage_tests.system.shutdown_tests import ShutdownTests
import unittest

if __name__ == '__main__':
    print('=====> Running all test in "sickrage_tests" <=====')

    TEST_CLASSES = [
        ComingEpisodesTests,
        CommonTests,
        HistoryTests,
        QualityTests,
        RestartTests,
        ShowTests,
        ShutdownTests,
    ]

    for test_class in TEST_CLASSES:
        SUITE = unittest.TestLoader().loadTestsFromTestCase(test_class)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
