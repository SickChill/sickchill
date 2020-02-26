# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# 2019-11-29 : Updated by Benj to comply with Tvdb API V3
# 2019-12-01 : Made sure update will be done when the cache is empty
#    or the last update is more then a week old.
#    Also remove the hardcoded api key and use the one from indexer_config
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
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import datetime
import threading
import time

# First Party Imports
import sickbeard
import sickchill
from sickbeard import db, logger, network_timezones, ui
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex


class ShowUpdater(object):
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

        self.seven_days = 7*24*60*60

    def run(self, force=False):
        if self.amActive:
            return

        self.amActive = True
        try:
            logger.log('ShowUpdater for tvdb Api V3 starting')

            cache_db_con = db.DBConnection('cache.db')
            for index, provider in sickchill.indexer:
                database_result = cache_db_con.select('SELECT `time` FROM lastUpdate WHERE provider = ?', [provider.name])
                last_update = int(database_result[0][0]) if database_result else 0
                network_timezones.update_network_dict()
                update_timestamp = int(time.time())
                updated_shows = []

                if last_update:
                    logger.log('Last update: {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update))))
                    # We query tvdb for updates starting from the last update time from the cache until now with increments of 7 days
                    for fromTime in range(last_update, update_timestamp - self.seven_days, self.seven_days):  # increments of 604800 sec = 7*24*60*60
                        try:
                            TvdbData = sickchill.indexer[1].updates(fromTime=fromTime, toTime=fromTime + self.seven_days)
                            TvdbData.series()
                            updated_shows.extend([d['id'] for d in TvdbData.series])
                        except Exception as error:
                            logger.log(str(error))
                else:
                    logger.log(_('No last update time from the cache, so we do a full update for all shows'))

                pi_list = []
                for cur_show in sickbeard.showList:
                    try:
                        cur_show.nextEpisode()

                        # Skip ended shows until interval is met
                        if cur_show.status == 'Ended' and sickbeard.ENDED_SHOWS_UPDATE_INTERVAL != 0:  # 0 is always
                            if sickbeard.ENDED_SHOWS_UPDATE_INTERVAL == -1:  # Never
                                continue
                            if (datetime.datetime.today() - datetime.datetime.fromordinal(cur_show.last_update_indexer or 1)).days < \
                                sickbeard.ENDED_SHOWS_UPDATE_INTERVAL:
                                continue

                        # Just update all of the shows for now until they fix the updates api
                        # When last_update is not set from the cache or the show was in the tvdb updated list we update the show
                        if 1 or not last_update or cur_show.indexerid in updated_shows:
                            pi_list.append(sickbeard.showQueueScheduler.action.update_show(cur_show, True))
                        else:
                            pi_list.append(sickbeard.showQueueScheduler.action.refresh_show(cur_show, force))
                    except (CantUpdateShowException, CantRefreshShowException) as error:
                        logger.log(_('Automatic update failed: {0}').format(ex(error)))

                ui.ProgressIndicators.setIndicator('dailyUpdate', ui.QueueProgressIndicator('Daily Update', pi_list))

                if database_result:
                    cache_db_con.action('UPDATE lastUpdate SET `time` = ? WHERE provider = ?', [str(update_timestamp), provider.name])
                else:
                    cache_db_con.action('INSERT INTO lastUpdate (time, provider) VALUES (?, ?)', [str(update_timestamp), provider.name])
        except Exception as error:
            logger.log(ex(error), logger.ERROR)

        self.amActive = False

    @staticmethod
    def request_hook(response, **kwargs):
        logger.log('{0} URL: {1} [Status: {2}]'.format
                   (response.request.method, response.request.url, response.status_code))

    def __del__(self):
        pass
