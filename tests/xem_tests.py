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

    def test_formating(self):
        self.loadFromDB()
        show = sickbeard.helpers.findCertainShow(sickbeard.showList, 24749)
        ep = show.getEpisode(21, 17)
        ep.airdate = datetime.date.today()

        # parse the file name
        pattern = u'%SN - %A-D - %EN'
        title = 'Show.Name.9th.Mar.2010.HDTV.XviD-RLSGROUP'
        try:
            myParser = NameParser(False, 1)
            parse_result = myParser.parse(title, True)
        except InvalidNameException:
            print(u"Unable to parse the filename " + ep.name + " into a valid episode")

        print parse_result

        search_string = {'Episode':[]}
        episode = ep.airdate
        str(episode).replace('-', '|')
        ep_string = sanitizeSceneName(show.name) + ' ' + \
                    str(episode).replace('-', '|') + '|' + \
                    episode.strftime('%b')

        search_string['Episode'].append(ep_string)

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

if __name__ == "__main__":
    print "=================="
    print "STARTING - XEM Scene Numbering TESTS"
    print "=================="
    print "######################################################################"
    suite = unittest.TestLoader().loadTestsFromTestCase(XEMBasicTests)