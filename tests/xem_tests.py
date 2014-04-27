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

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib'))

import test_lib as test
import sickbeard
from sickbeard.helpers import sanitizeSceneName
from sickbeard.show_name_helpers import allPossibleShowNames
from sickbeard.tv import TVShow

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

    def test_formating(self):
        self.loadFromDB()
        show = sickbeard.helpers.findCertainShow(sickbeard.showList, 111051)
        ep = show.getEpisode(2014, 34)

        scene_ep_string = sanitizeSceneName(show.name) + ' ' + \
                    sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep.scene_season,
                                                          'episodenumber': ep.scene_episode} + '|' + \
                    sickbeard.config.naming_ep_type[0] % {'seasonnumber': ep.scene_season,
                                                          'episodenumber': ep.scene_episode} + '|' + \
                    sickbeard.config.naming_ep_type[3] % {'seasonnumber': ep.scene_season,
                                                          'episodenumber': ep.scene_episode} + ' %s category:tv' % ''

        scene_season_string = show.name + ' S%02d' % int(ep.scene_season) + ' -S%02d' % int(ep.scene_season) + 'E' + ' category:tv'  #1) ShowName SXX -SXXE

        print(
            u'Searching "%s" for "%s" as "%s"' % (show.name, ep.prettyName(), ep.scene_prettyName()))

        print('Scene episode search strings: %s' % (scene_ep_string))

        print('Scene season search strings: %s' % (scene_season_string))

    def test_renaming(self):
        self.file_name = 'American Pickers - S04E01 - Jurassic Pick.avi'
        orig_extension = self.file_name.rpartition('.')[-1]
        new_base_name = os.path.basename(proper_path)
        new_file_name = new_base_name + '.' + orig_extension

if __name__ == "__main__":
    print "=================="
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)