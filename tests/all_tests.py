#!/usr/bin/env python2.7
# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
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

"""
Perform all tests in tests/
"""

# pylint: disable=line-too-long

import fnmatch
import os
import sys
import unittest


TESTS_DIR = os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

sys.path.insert(1, os.path.join(TESTS_DIR, '../lib'))
sys.path.insert(1, os.path.join(TESTS_DIR, '..'))


class AllTests(unittest.TestCase):
    """
    Performs all tests in tests directory.

    Methods
        setUp
        test_all
        _get_module_strings
        _get_test_files
        _get_test_suites
    """
    # Block issue_submitter_tests to avoid issue tracker spam on every build
    blacklist = [TESTS_DIR + 'all_tests.py', TESTS_DIR + 'issue_submitter_tests.py', TESTS_DIR + 'search_tests.py']

    def setUp(self):
        """
        Get all tests
        """
        self.test_file_strings = self._get_test_files()
        self.module_strings = self._get_module_strings()
        self.suites = self._get_test_suites()
        self.test_suite = unittest.TestSuite(self.suites)

    def test_all(self):
        """
        Perform all tests
        """
        print "===================="
        print "STARTING - ALL TESTS"
        print "===================="

        for included_files in self.test_file_strings:
            print "- " + included_files[len(TESTS_DIR):-3]

        text_runner = unittest.TextTestRunner().run(self.test_suite)
        if not text_runner.wasSuccessful():
            sys.exit(-1)

    def _get_module_strings(self):
        """
        Convert the file names into module names

        :return: all module names
        """
        modules = []
        for file_string in self.test_file_strings:
            modules.append(file_string[len(TESTS_DIR):len(file_string) - 3].replace(os.sep, '.'))

        return modules

    def _get_test_files(self):
        """
        Get the name of all the tests in the tests directory

        :return: all file names that match
        """
        matches = []
        for root, _, file_names in os.walk(TESTS_DIR):
            for filename in fnmatch.filter(file_names, '*_tests.py'):
                filename_with_path = os.path.join(root, filename)

                if filename_with_path not in self.blacklist:
                    matches.append(filename_with_path)

        return matches

    def _get_test_suites(self):
        """
        Load all test suites

        :return: all test suites from tests
        """
        return [unittest.defaultTestLoader.loadTestsFromName(file_string) for file_string in self.module_strings]

if __name__ == "__main__":
    unittest.main()
