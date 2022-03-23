"""
Test XEM
"""

import re
import unittest

import sickchill.oldbeard.db
from sickchill import settings
from sickchill.tv import TVShow
from tests import conftest


class XEMBasicTests(conftest.SickChillTestDBCase):
    """
    Perform basic xem tests
    """

    @staticmethod
    def test_load_from_db():
        """
        Populates the showList with shows from the database
        """
        test_main_db_con = sickchill.oldbeard.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
            settings.showList.append(cur_show)


if __name__ == "__main__":
    print("==================")
    print("STARTING - XEM Scene Numbering TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
