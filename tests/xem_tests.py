# coding=UTF-8
# Author: Dennis Lutter <lad1337@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import unittest
import sys, os.path
import datetime

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import test_lib as test
import sickbeard
from sickbeard.helpers import sanitizeSceneName
from sickbeard.name_parser.parser import NameParser
from sickbeard.tv import TVShow

class XEMBasicTests(test.SickbeardTestDBCase):
    def loadShowsFromDB(self):
        """
        Populates the showList with shows from the database
        """

        myDB = test.db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_shows")

        for sqlShow in sqlResults:
            try:
                curShow = TVShow(int(sqlShow["indexer"]), int(sqlShow["indexer_id"]))
                sickbeard.showList.append(curShow)
            except Exception:
                pass

    def loadFromDB(self):
        """
        Populates the showList with shows from the database
        """

        myDB = test.db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_shows")

        for sqlShow in sqlResults:
            try:
                curShow = TVShow(int(sqlShow["indexer"]), int(sqlShow["indexer_id"]))
                sickbeard.showList.append(curShow)
            except Exception, e:
                print "There was an error creating the show"

    def test_formating(self):
        release = "UFC.172.26th.April.2014.HDTV.x264.720p-Sir.Paul[rartv]"
        # parse the name to break it into show name, season, and episode
        np = NameParser(file)
        parse_result = np.parse(release).convert()

        print(parse_result)

if __name__ == "__main__":
    print "=================="
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)