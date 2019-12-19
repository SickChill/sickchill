# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# 2019-11-29 : Updated by Benj to comply with Tvdb API V3
# 2019-12-01 : Made sure update will be done when the cache is empty
#              or the last update is more then a week old.
#              Also remove the hardcoded api key and use the one from indexer_config
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
import json
import threading
import time

import sickbeard
from sickbeard import db, helpers, logger, network_timezones, ui
from sickbeard.indexers.indexer_config import INDEXER_TVDB, INDEXER_TVRAGE
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex


class ShowUpdater(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False

        self.apikey = json.dumps({'apikey':sickbeard.indexerApi(INDEXER_TVDB).api_params['apikey']})
        self.base = 'https://api.thetvdb.com'
        self.login = self.base + '/login'
        self.update = self.base + '/updated/query?fromTime='
        self.session = helpers.make_session()
            # set the correct headers for the requests calls to tvdb
        self.session.headers.update({'Accept': 'application/json','Content-Type': 'application/json'})
        self.timeout = 12.1 #General timeout for the requests calls to prevent a hang if tvdb does not respond

    def _gettoken(self):
        logger.log('Login to tvdb to get a token')
        Token = None
        try:
            resp = self.session.post(self.login, self.apikey, timeout=self.timeout)
            if resp.ok:
                    # Put the token in the request header
                Token = json.loads(resp.text).get('token','')
                self.session.headers.update({"Authorization": "Bearer " + Token})
                return True
            else:
                raise Exception('Failed to login on tvdb. reason: %s' % resp.reason)
        except Exception as error:
            logger.log(str(error))
            return False

    def run(self, force=False):  # pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements
        logger.log('ShowUpdater for tvdb Api V3 starting')
        if self.amActive:
            return
        self.amActive = True
        if not self._gettoken():
            self.amActive = False
            logger.log('No token from tvdb so update not possible')
            return 

        cache_db_con = db.DBConnection('cache.db')
        result = cache_db_con.select('SELECT `time` FROM lastUpdate WHERE provider = ?', ['theTVDB'])
        last_update = int(result[0][0]) if result else 0
        network_timezones.update_network_dict()
        update_timestamp = int(time.time())
        updated_shows = []
        if last_update:
            logger.log( 'Last update: %s' %time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_update)))
                # We query tvdb for updates starting from the last update time from the cache until now with increments of 7 days
            for fromTime in range(last_update, update_timestamp, 604800): # increments of 604800 sec = 7*24*60*60
                try:                    
                    resp = self.session.get(self.update + str(fromTime), timeout=self.timeout)
                    if resp.ok:
                        TvdbData = json.loads(resp.text)
                        updated_shows.extend([d['id'] for d in TvdbData.get('data',[])])
                    else:
                        raise Exception('Failed to get update from tvdb. reason: %s' % resp.reason)
                except Exception as error:
                    logger.log(str(error))
        else:
            logger.log('No last update time from the cache, so we do a full update for all shows')
        pi_list = []
        for cur_show in sickbeard.showList:
            if int(cur_show.indexer) in [INDEXER_TVRAGE]:
                logger.log('Indexer is no longer available for show [{0}] '.format(cur_show.name), logger.WARNING)
                continue
            try:
                cur_show.nextEpisode()
                if sickbeard.indexerApi(cur_show.indexer).name == 'theTVDB':
                        # When last_update is not set from the cache or the show was in the tvdb updated list we update the show
                    if not last_update or cur_show.indexerid in updated_shows:
                        pi_list.append(sickbeard.showQueueScheduler.action.update_show(cur_show, True))
                    else:
                        pi_list.append(sickbeard.showQueueScheduler.action.refresh_show(cur_show, False))
            except (CantUpdateShowException, CantRefreshShowException) as error:
                logger.log('Automatic update failed: {0}'.format(ex(error)))

        ui.ProgressIndicators.setIndicator('dailyUpdate', ui.QueueProgressIndicator('Daily Update', pi_list))

        cache_db_con.action('UPDATE lastUpdate SET `time` = ? WHERE provider=?', [str(update_timestamp), 'theTVDB'])

        self.amActive = False

    @staticmethod
    def request_hook(response, **kwargs):
        _ = kwargs
        logger.log('{0} URL: {1} [Status: {2}]'.format
                   (response.request.method, response.request.url, response.status_code))

    def __del__(self):
        pass
