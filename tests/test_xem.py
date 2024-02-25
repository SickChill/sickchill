"""
Test XEM
"""

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
    def load_shows_from_db():
        """
        Populates the show_list with shows from the database
        """

        test_main_db_con = sickchill.oldbeard.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            # noinspection PyBroadException
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                settings.show_list.append(cur_show)
            except Exception:
                pass

    @staticmethod
    def load_from_db():
        """
        Populates the show_list with shows from the database
        """
        test_main_db_con = sickchill.oldbeard.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                settings.show_list.append(cur_show)
            except Exception as error:
                print(f"There was an error creating the show {error}")


if __name__ == "__main__":
    print("==================")
    print("STARTING - XEM Scene Numbering TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
