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
Test KAT Result Parsing
"""

from __future__ import print_function, unicode_literals

import sys

import unittest
from thepiratebay import ThePirateBayParsingTests

# Have to do this before importing sickbeard
sys.path.insert(1, 'lib')

import sickbeard

overwrite_cassettes = False


class KATParsingTests(ThePirateBayParsingTests):
    pass

if __name__ == '__main__':
    print('=====> Testing %s', __file__)

    def override_log(msg, *args, **kwargs):
        """Override the SickRage logger so we can see the debug output from providers"""
        _ = args, kwargs
        print(msg)

    sickbeard.logger.log = override_log

    test_suite = unittest.TestLoader().loadTestsFromTestCase(KATParsingTests)
    unittest.TextTestRunner(verbosity=3).run(test_suite)
