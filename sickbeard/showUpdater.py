# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
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

import xml.etree.ElementTree as ET
import requests
import time
import datetime
import threading
import sickbeard

from sickbeard import logger
from sickbeard import ui
from sickbeard import db
from sickbeard import network_timezones
from sickbeard import failed_history
from sickbeard import helpers
from sickrage.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex
from sickbeard.indexers.indexer_config import INDEXER_TVRAGE
from sickbeard.indexers.indexer_config import INDEXER_TVDB


class ShowUpdater(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

        self.session = requests.Session()

    def run(self, force=False):  # pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements

        if self.amActive:
            return

        self.amActive = True

        update_datetime = datetime.datetime.now()
        # update_date = update_datetime.date()

        update_timestamp = time.mktime(update_datetime.timetuple())
        cache_db_con = db.DBConnection('cache.db')
        result = cache_db_con.select("SELECT `time` FROM lastUpdate WHERE provider = 'theTVDB'")
        if result:
            last_update = long(result[0]['time'])
        else:
            last_update = update_timestamp - 691200
            cache_db_con.action("INSERT INTO lastUpdate (provider,`time`) VALUES (?, ?)", ['theTVDB', last_update])

        # refresh network timezones
        network_timezones.update_network_dict()

        # sure, why not?
        if sickbeard.USE_FAILED_DOWNLOADS:
            failed_history.trimHistory()

        update_delta = update_timestamp - last_update

        if update_delta >= 691200:      # 8 days ( 7 days + 1 day of buffer time)
            update_file = 'updates_month.xml'
        elif update_delta >= 90000:     # 25 hours ( 1 day + 1 hour of buffer time)
            update_file = 'updates_week.xml'
        else:
            update_file = 'updates_day.xml'

        url = 'http://thetvdb.com/api/%s/updates/%s' % (sickbeard.indexerApi(INDEXER_TVDB).api_params['apikey'], update_file)
        data = helpers.getURL(url, session=self.session, returns='text')
        if not data:
            logger.log(u"Could not get the recently updated show data from %s. Retrying later. Url was: %s" % (sickbeard.indexerApi(INDEXER_TVDB).name, url))
            self.amActive = False
            return

        updated_shows = []
        try:
            tree = ET.fromstring(data)
            for show in tree.findall("Series"):
                updated_shows.append(int(show.find('id').text))
        except SyntaxError:
            update_timestamp = last_update

        pi_list = []
        for cur_show in sickbeard.showList:
            if int(cur_show.indexer) in [INDEXER_TVRAGE]:
                logger.log(u"Indexer is no longer available for show [ %s ] " % cur_show.name, logger.WARNING)
                continue

            try:
                cur_show.nextEpisode()
                if sickbeard.indexerApi(cur_show.indexer).name == 'theTVDB':
                    if cur_show.indexerid in updated_shows:
                        if (update_datetime - datetime.datetime.fromordinal(cur_show.last_update_indexer)).seconds >= 43200:
                            pi_list.append(sickbeard.showQueueScheduler.action.updateShow(cur_show, True))
                # else:
                #     if cur_show.should_update(update_date=update_date):
                #         try:
                #             pi_list.append(sickbeard.showQueueScheduler.action.updateShow(cur_show, True))
                #         except CantUpdateShowException as e:
                #             logger.log(u"Unable to update show: {0}".format(str(e)), logger.DEBUG)
                #     else:
                #         logger.log(
                #             u"Not updating episodes for show " + cur_show.name + " because it's last/next episode is not within the grace period.",
                #             logger.DEBUG)
            except (CantUpdateShowException, CantRefreshShowException) as e:
                logger.log(u"Automatic update failed: " + ex(e), logger.ERROR)

        ui.ProgressIndicators.setIndicator('dailyUpdate', ui.QueueProgressIndicator("Daily Update", pi_list))

        cache_db_con.action("UPDATE lastUpdate SET `time` = ? WHERE provider=?", [update_timestamp, 'theTVDB'])

        self.amActive = False

    def __del__(self):
        pass
