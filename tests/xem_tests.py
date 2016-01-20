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
Test XEM
"""

# pylint: disable=line-too-long

import os.path
import re
import sys
import unittest

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard.tv import TVShow
import sickbeard
import tests.test_lib as test


class XEMBasicTests(test.SickbeardTestDBCase):
    """
    Perform basic xem tests
    """

    @staticmethod
    def load_shows_from_db():
        """
        Populates the showList with shows from the database
        """

        test_main_db_con = test.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                sickbeard.showList.append(cur_show)
            except Exception:  # pylint: disable=broad-except
                pass

    @staticmethod
    def load_from_db():
        """
        Populates the showList with shows from the database
        """
        test_main_db_con = test.db.DBConnection()
        sql_results = test_main_db_con.select("SELECT * FROM tv_shows")

        for sql_show in sql_results:
            try:
                cur_show = TVShow(int(sql_show["indexer"]), int(sql_show["indexer_id"]))
                sickbeard.showList.append(cur_show)
            except Exception as error:  # pylint: disable=broad-except
                print "There was an error creating the show %s" % error

    @staticmethod
    def test_formatting():
        """
        Test formatting
        """
        name = "Game.of.Thrones.S03.720p.HDTV.x264-CtrlHD"
        release = "Game of Thrones"

        # m = re.match('(?P<ep_ab_num>(?>\d{1,3})(?![ip])).+', name)

        # pylint: disable=anomalous-backslash-in-string
        escaped_name = re.sub('\\\\[\\s.-]', '\W+', re.escape(release))
        # pylint: disable=anomalous-backslash-in-string
        cur_regex = '^' + escaped_name + '\W+(?:(?:S\d[\dE._ -])|(?:\d\d?x)|(?:\d{4}\W\d\d\W\d\d)|(?:(?:part|pt)[\._ -]?(\d|[ivx]))|Season\W+\d+\W+|E\d+\W+|(?:\d{1,3}.+\d{1,}[a-zA-Z]{2}\W+[a-zA-Z]{3,}\W+\d{4}.+))'
        # print(u"Checking if show " + name + " matches " + curRegex)

        match = re.search(cur_regex, name, re.I)
        if match:
            # print(u"Matched " + curRegex + " to " + name)
            pass


if __name__ == "__main__":
    print "=================="
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"

    SUITE = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
