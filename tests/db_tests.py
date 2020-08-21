"""
Test show database functionality.

Tests:
    DBBasicTests
    DBMultiTests
"""
import threading
import time
import unittest
from datetime import datetime

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
        super().setUp()
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
        super().setUp()
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


class CacheDBTests(test.SickChillTestDBCase):
    def setUp(self):
        super().setUp()
        self.cache_db_con = sickchill.oldbeard.db.DBConnection('cache.db')
        sickchill.oldbeard.db.upgrade_database(self.cache_db_con, sickchill.oldbeard.databases.cache.InitialSchema)

        cur_timestamp = int(time.mktime(datetime.today().timetuple()))
        self.record = (
            {
                'provider': 'provider',
                'name': 'name',
                'season': 1,
                'episodes': '|1|',
                'indexerid': 1,
                'url': 'url',
                'time': cur_timestamp,
                'quality': '1',
                'release_group': 'SICKCHILL',
                'version': 1,
                'seeders': 1,
                'leechers': 1,
                'size': 1
            },
            {'url': 'url'}
        )

        self.cache_db_con.action("DELETE FROM results")
        query = 'INSERT OR IGNORE INTO results ({col}) VALUES ({rep})'.format(col=', '.join(self.record[0].keys()), rep=', '.join(['?'] * len(self.record[0])))
        self.cache_db_con.action(query, list(self.record[0].values()))

    def test_mass_upsert(self):
        def num_rows():
            return len(self.cache_db_con.select('SELECT url FROM results'))
        self.assertEqual(num_rows(), 1, num_rows())

        self.cache_db_con.upsert('results', self.record[0], self.record[1])
        self.assertEqual(num_rows(), 1, )

        self.cache_db_con.mass_upsert('results', [self.record], log_transaction=True)
        self.assertEqual(num_rows(), 1)

        self.record[0]['url'] = self.record[1]['url'] = 'new_url'

        self.cache_db_con.upsert('results', self.record[0], self.record[1])
        self.assertEqual(num_rows(), 2)

        self.cache_db_con.mass_upsert('results', [self.record], log_transaction=True)
        self.assertEqual(num_rows(), 2)

        self.cache_db_con.upsert('results', self.record[0], self.record[1])
        self.assertEqual(num_rows(), 2)

        self.record[0]['url'] = self.record[1]['url'] = 'third_url'
        self.record[0]['seeders'] = 9999
        self.cache_db_con.mass_upsert('results', [self.record], log_transaction=True)
        self.assertEqual(num_rows(), 3)

        self.cache_db_con.upsert('results', self.record[0], self.record[1])
        self.assertEqual(num_rows(), 3)

        self.cache_db_con.mass_upsert('results', [self.record], log_transaction=True)
        self.assertEqual(num_rows(), 3)

        results = self.cache_db_con.select("SELECT * FROM results WHERE url = ?", [self.record[1]['url']])

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], self.record[0]['url'])
        self.assertEqual(results[0]['seeders'], self.record[0]['seeders'])

        results = self.cache_db_con.select("SELECT * FROM results WHERE url = 'url'")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['url'], 'url')
        self.assertNotEqual(results[0]['url'], self.record[0]['url'])

        self.assertEqual(results[0]['seeders'], 1)
        self.assertNotEqual(results[0]['seeders'], self.record[0]['seeders'])

        self.assertEqual(num_rows(), 3)


if __name__ == '__main__':
    print("==================")
    print("STARTING - DB TESTS")
    print("==================")
    print("######################################################################")
    SUITE = unittest.TestLoader().loadTestsFromTestCase(DBBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)

    # suite = unittest.TestLoader().loadTestsFromTestCase(DBMultiTests)
    # unittest.TextTestRunner(verbosity=2).run(suite)
