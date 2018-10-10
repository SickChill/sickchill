# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sick-rage.github.io
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
Tests for SickChill
"""

from __future__ import print_function

import helper
import media
import providers
import show
import system
import unittest

if __name__ == '__main__':
    print('=====> Running all test in "sickchill_tests" <=====')

    TEST_MODULES = [
        helper,
        media,
        providers,
        show,
        system,
    ]

    for test_module in TEST_MODULES:
        SUITE = unittest.TestLoader().loadTestsFromModule(test_module)
        unittest.TextTestRunner(verbosity=2).run(SUITE)
