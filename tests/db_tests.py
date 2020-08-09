"""
Test show database functionality.

Tests:
    DBBasicTests
    DBMultiTests
"""

import threading
import unittest

import sickchill.oldbeard
from tests import test_lib as test


class DBBasicTests(test.SickChillTestDBCase):
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
        self.sr_db = sickchill.oldbeard.db.DBConnection()

    def test_select(self):
        """
        Test selecting from the database
        """
        self.sr_db.select("SELECT * FROM tv_episodes WHERE showid = ? AND location != ''", [0000])


class DBMultiTests(test.SickChillTestDBCase):
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
        self.sr_db = sickchill.oldbeard.db.DBConnection()

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
