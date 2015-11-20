# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickrage.tv
# Git: https://github.com/SickRage/SickRage.git
#
# This file is part of SickRage.
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

from helper.quality_tests import QualityTests
from show.coming_episodes_tests import ComingEpisodesTests
from show.history_tests import HistoryTests
from system.restart_tests import RestartTests
from system.shutdown_tests import ShutdownTests
from unittest import TestLoader, TextTestRunner

if __name__ == '__main__':
    print('=====> Running all test <=====')

    test_classes = [
        ComingEpisodesTests,
        HistoryTests,
        QualityTests,
        RestartTests,
        ShutdownTests
    ]

    for test_class in test_classes:
        suite = TestLoader().loadTestsFromTestCase(test_class)
        TextTestRunner(verbosity=2).run(suite)
