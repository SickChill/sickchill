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

import sys, os.path

tests_dir=os.path.abspath(__file__)[:-len(os.path.basename(__file__))]

sys.path.insert(1, os.path.join(tests_dir, '../lib'))
sys.path.insert(1, os.path.join(tests_dir, '..'))

import glob
import unittest

class AllTests(unittest.TestCase):
    #Block issue_submitter_tests to avoid issue tracker spam on every build
    blacklist = [tests_dir + 'all_tests.py', tests_dir + 'issue_submitter_tests.py', tests_dir + 'search_tests.py']
    def setUp(self):
        self.test_file_strings = [ x for x in glob.glob(tests_dir + '*_tests.py') if not x in self.blacklist ]
        self.module_strings = [file_string[len(tests_dir):len(file_string) - 3] for file_string in self.test_file_strings]
        self.suites = [unittest.defaultTestLoader.loadTestsFromName(file_string) for file_string in self.module_strings]
        self.testSuite = unittest.TestSuite(self.suites)

    def testAll(self):
        print "=================="
        print "STARTING - ALL TESTS"
        print "=================="
        for includedfiles in self.test_file_strings:
            print "- " + includedfiles[len(tests_dir):-3]

        text_runner = unittest.TextTestRunner().run(self.testSuite)
        if not text_runner.wasSuccessful():
            sys.exit(-1)

if __name__ == "__main__":
    unittest.main()
