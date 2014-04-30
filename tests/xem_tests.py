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
from sickbeard.tv import TVShow
from sickbeard.name_parser.parser import NameParser, InvalidNameException

class XEMBasicTests(test.SickbeardTestDBCase):
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

    def test_parsing_scene_release(self):
        self.loadFromDB()

        # parse the file name
        scene_parsse_results1 = ''
        scene_parsse_results2 = ''
        scene_release = 'Pawn Stars S08E41 Field Trip HDTV x264-tNe'
        try:
            myParser = NameParser(False, 1)
            scene_parsse_results1 = myParser.parse(scene_release)
            scene_parsse_results2 = myParser.parse(scene_release).convert()
        except InvalidNameException:
            print(u"Unable to parse the filename " + scene_release + " into a valid episode")

        print scene_parsse_results1
        print scene_parsse_results2

if __name__ == "__main__":
    print "=================="
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)