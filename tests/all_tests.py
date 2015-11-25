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

import fnmatch
import os
import sys
import unittest

tests_dir = os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

sys.path.insert(1, os.path.join(tests_dir, '../lib'))
sys.path.insert(1, os.path.join(tests_dir, '..'))


class AllTests(unittest.TestCase):
    # Block issue_submitter_tests to avoid issue tracker spam on every build
    blacklist = [tests_dir + 'all_tests.py', tests_dir + 'issue_submitter_tests.py', tests_dir + 'search_tests.py']

    def setUp(self):
        self.test_file_strings = self._get_test_files()
        self.module_strings = self._get_module_strings()
        self.suites = self._get_test_suites()
        self.testSuite = unittest.TestSuite(self.suites)

    def testAll(self):
        print "===================="
        print "STARTING - ALL TESTS"
        print "===================="

        for included_files in self.test_file_strings:
            print "- " + included_files[len(tests_dir):-3]

        text_runner = unittest.TextTestRunner().run(self.testSuite)
        if not text_runner.wasSuccessful():
            sys.exit(-1)

    def _get_module_strings(self):
        modules = []
        for file_string in self.test_file_strings:
            modules.append(file_string[len(tests_dir):len(file_string) - 3].replace(os.sep, '.'))

        return modules

    def _get_test_files(self):
        matches = []
        for root, _, file_names in os.walk(tests_dir):
            for filename in fnmatch.filter(file_names, '*_tests.py'):
                filename_with_path = os.path.join(root, filename)

                if filename_with_path not in self.blacklist:
                    matches.append(filename_with_path)

        return matches

    def _get_test_suites(self):
        return [unittest.defaultTestLoader.loadTestsFromName(file_string) for file_string in self.module_strings]


if __name__ == "__main__":
    unittest.main()
