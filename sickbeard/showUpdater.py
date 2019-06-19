# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import threading
import time

import sickbeard
from sickbeard import db, helpers, logger, network_timezones, ui
from sickbeard.indexers.indexer_config import INDEXER_TVDB, INDEXER_TVRAGE
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex

try:
    import xml.etree.cElementTree as etree
except ImportError:
    import xml.etree.ElementTree as etree




class ShowUpdater(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

        self.session = helpers.make_session()

    def run(self, force=False):  # pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements

        if self.amActive:
            return

        self.amActive = True

        update_timestamp = time.mktime(datetime.datetime.now().timetuple())
        cache_db_con = db.DBConnection('cache.db')
        result = cache_db_con.select('SELECT `time` FROM lastUpdate WHERE provider = ?', ['theTVDB'])
        if result:
            last_update = int(result[0][0])
        else:
            last_update = int(time.mktime(datetime.datetime.min.timetuple()))
            cache_db_con.action('INSERT INTO lastUpdate (provider, `time`) VALUES (?, ?)', ['theTVDB', last_update])

        network_timezones.update_network_dict()

        url = 'http://thetvdb.com/api/Updates.php?type=series&time={0}'.format(last_update)
        data = helpers.getURL(url, session=self.session, returns='text', hooks={'response': self.request_hook})
        if not data:
            logger.log('Could not get the recently updated show data from {0}. Retrying later. Url was: {1}'.format(sickbeard.indexerApi(INDEXER_TVDB).name, url))
            self.amActive = False
            return

        updated_shows = set()
        try:
            tree = etree.fromstring(data)
            for show in tree.findall('Series'):
                updated_shows.add(int(show.text))
        except SyntaxError:
            update_timestamp = last_update

        pi_list = []
        for cur_show in sickbeard.showList:
            if int(cur_show.indexer) in [INDEXER_TVRAGE]:
                logger.log('Indexer is no longer available for show [{0}] '.format(cur_show.name), logger.WARNING)
                continue

            try:
                cur_show.nextEpisode()
                if sickbeard.indexerApi(cur_show.indexer).name == 'theTVDB':
                    if cur_show.indexerid in updated_shows:
                        pi_list.append(sickbeard.show_queue_scheduler.action.update_show(cur_show, True))
                    else:
                        pi_list.append(sickbeard.show_queue_scheduler.action.refresh_show(cur_show, False))
            except (CantUpdateShowException, CantRefreshShowException) as error:
                logger.log('Automatic update failed: {0}'.format(ex(error)), logger.DEBUG)

        ui.ProgressIndicators.setIndicator('dailyUpdate', ui.QueueProgressIndicator('Daily Update', pi_list))

        cache_db_con.action('UPDATE lastUpdate SET `time` = ? WHERE provider=?', [update_timestamp, 'theTVDB'])

        self.amActive = False

    @staticmethod
    def request_hook(response, **kwargs):
        _ = kwargs
        logger.log('{0} URL: {1} [Status: {2}]'.format
                   (response.request.method, response.request.url, response.status_code), logger.DEBUG)

    def __del__(self):
        pass
