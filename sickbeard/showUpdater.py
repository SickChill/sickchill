# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# 2019-11-29 : Updated by Benj to comply with Tvdb API V3
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
import json

import sickbeard
from sickbeard import db, helpers, logger, network_timezones, ui
from sickbeard.indexers.indexer_config import INDEXER_TVDB, INDEXER_TVRAGE
from sickchill.helper.exceptions import CantRefreshShowException, CantUpdateShowException, ex


class ShowUpdater(object):  # pylint: disable=too-few-public-methods
    def __init__(self):
        self.lock = threading.Lock()
        self.amActive = False
        self.base = 'https://api.thetvdb.com'
        self.apikey = json.dumps({'apikey':"F9C450E78D99172E"})
        self.login = self.base + '/login'
        self.refresh = self.base + '/refresh'
        self.update = self.base + '/updated/query?fromTime='
        self.session = helpers.make_session()
            # set the correct headers for the requests calls to tvdb
        self.session.headers.update({'Accept': 'application/json','Content-Type': 'application/json','Authorization': ''})
        self.timeout = 12.1 #General timeout for the requests calls to prevent a hang if tvdb does not fespond

    def _gettoken(self):
        try:
            if self.session.headers.get('Authorization'):
                    # There is a token in the header so we try to refresh it
                resp = self.session.get(self.refresh, timeout=self.timeout)
                logger.log('Try to refresh a tvdb token')
                if resp.ok:
                    Token = json.loads(resp.text).get('token','')
                    self.session.headers.update({"Authorization": "Bearer " + Token})
                    logger.log('Tvdb token refreshed')
                    return True
                # there was no token in the header or the token was expired so we login to tvdb with the apikey to get a new token
            logger.log('Try to login to tvdb to get a token')
            resp = self.session.post(self.login, self.apikey, timeout=self.timeout)
            if resp.ok:
                Token = json.loads(resp.text).get('token','')
                self.session.headers.update({"Authorization": "Bearer " + Token})
                logger.log('Logged in on tvdb and got a token.')
                return True
            else:
                logger.log('Failed to get a token from tvdb')
                return False
        except Exception as error:
            logger.log('Could not get a token from Tvdb. Reason: %s' %resp.reason)
        return False

    def run(self, force=False):  # pylint: disable=unused-argument, too-many-locals, too-many-branches, too-many-statements
        logger.log('ShowUpdater for tvdb Api V3 starting')
        if self.amActive:
            return
            # get a tvdb api token and put it in the requests session header
        if not self._gettoken():
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
        try:
            logger.log('Tvdb Cmd:' + self.update + str(last_update))
            resp = self.session.get(self.update + str(last_update), timeout=self.timeout)
        except Exception as error:
            self.amActive = False
            logger.log('Could not get show updates from tvdb. Reason: %s' %resp.reason)
            return
        TvdbData = json.loads(resp.text)
        if TvdbData.get('Error'):
            logger.log(TvdbData['Error'])
            self.amActive = False
            return
        else:
                # Use a list comprehension to put all the updated serie id's from the dict into a single list
            updated_shows = [i['id'] for i in TvdbData.get('data',[])]
            logger.log('Updates for: %s' % updated_shows )
        if not updated_shows:
            logger.log('No updated shows found on tvdb')
            self.amActive = False
            return

        pi_list = []
        for cur_show in sickbeard.showList:
            if int(cur_show.indexer) in [INDEXER_TVRAGE]:
                logger.log('Indexer is no longer available for show [{0}] '.format(cur_show.name), logger.WARNING)
                continue
            try:
                cur_show.nextEpisode()
                if sickbeard.indexerApi(cur_show.indexer).name == 'theTVDB':
                    if cur_show.indexerid in updated_shows:
                        pi_list.append(sickbeard.showQueueScheduler.action.update_show(cur_show, True))
                    else:
                        pi_list.append(sickbeard.showQueueScheduler.action.refresh_show(cur_show, False))
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
