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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

"""
Test show database functionality.

Tests:
    DBBasicTests
    DBMultiTests
"""

import os.path
import sys
import threading
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tests.test_lib as test


class DBBasicTests(test.SickbeardTestDBCase):
    """
    Perform basic database tests.

    Tests:
        test_select
    """

    def setUp(self):
        """
        Set up test.
        """
        super(DBBasicTests, self).setUp()
        self.sr_db = test.db.DBConnection()

    def test_select(self):
        """
        Test selecting from the database
        """
        self.sr_db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])


class DBMultiTests(test.SickbeardTestDBCase):
    """
    Perform multi-threaded test of the database

    Tests:
        test_threaded
    """
    def setUp(self):
        """
        Set up test.
        """
        super(DBMultiTests, self).setUp()
        self.sr_db = test.db.DBConnection()

    def select(self):
        """
        Select from the database.
        """
        self.sr_db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])

    def test_threaded(self):
        """
        Test multi-threaded selection from the database
        """
        for _ in range(4):
            thread = threading.Thread(target=self.select)
            thread.start()

if __name__ == '__main__':
    print("==================")
    print("STARTING - DB TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(DBBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    # suite = unittest.TestLoader().loadTestsFromTestCase(DBMultiTests)
    # unittest.TextTestRunner(verbosity=2).run(suite)
