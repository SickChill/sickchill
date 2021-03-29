"""
Test XEM
"""

import unittest

from tests import conftest

import sickchill.oldbeard.db
from sickchill import settings
from sickchill.tv import TVShow


class XEMBasicTests(conftest.SickChillTestDBCase):
    """
    Perform basic xem tests
    """

    @staticmethod
    def load_shows_from_db():
        """
        Populates the showList with shows from the database
        """

        test_main_db_con = sickchill.oldbeard.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                settings.showList.append(cur_show)
            except Exception:  # noqa: S110
                pass

    @staticmethod
    def load_from_db():
        """
        Populates the showList with shows from the database
        """
        test_main_db_con = sickchill.oldbeard.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                settings.showList.append(cur_show)
            except Exception as error:
                print("There was an error creating the show {0}".format(error))

    # @staticmethod
    # def test_formatting():
    #     """
    #     Test formatting
    #     """
    #     name = "Game.of.Thrones.S03.720p.HDTV.x264-CtrlHD"
    #     release = "Game of Thrones"
    #
    #     # m = re.match('(?P<ep_ab_num>(?>\d{1,3})(?![ip])).+', name)
    #
    #     escaped_name = re.sub('\\\\[\\s.-]', '\W+', re.escape(release))
    #     cur_regex = '^' + escaped_name + r'\W+(?:(?:S\d[\dE._ -])|' + \
    #         r'(?:\d\d?x)|(?:\d{4}\W\d\d\W\d\d)|(?:(?:part|pt)[\._ -]?(\d|[ivx]))|' + \
    #         r'Season\W+\d+\W+|E\d+\W+|(?:\d{1,3}.+\d{1,}[a-zA-Z]{2}\W+[a-zA-Z]{3,}\W+\d{4}.+))'
    #
    #     # print("Checking if show " + name + " matches " + curRegex)
    #
    #     match = re.search(cur_regex, name, re.I)
    #     if match:
    #         # print("Matched " + curRegex + " to " + name)
    #         pass


if __name__ == "__main__":
    print("==================")
    print("STARTING - XEM Scene Numbering TESTS")
    print("==================")
    print("######################################################################")

    SUITE = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
