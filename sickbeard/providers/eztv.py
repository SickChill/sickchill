# coding=utf-8
# Author: Nicolas Martinelli <nicolas.martinelli@gmail.com>
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

import traceback
import re, datetime

import generic
import sickbeard
from sickbeard import classes
from sickbeard import helpers
from sickbeard import logger, tvcache, db
from sickbeard.common import Quality

class EZTVProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "EZTV")

        self.supportsBacklog = False
        self.enabled = False
        self.ratio = None

        self.cache = EZTVCache(self)

        self.urls = {
            'base_url': 'http://eztvapi.re/',
            'show': 'http://eztvapi.re/show/%s',
        }

        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def seedRatio(self):
        return self.ratio

    def imageName(self):
        return 'eztv_bt_chat.png'

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        search_string['Episode'].append({
            'imdb_id': self.show.imdbid,
            'season': int(ep_obj.scene_season),
            'episode': int(ep_obj.scene_episode),
            'add_string': add_string,
        })

        return [search_string]

    def getQuality(self, item, anime=False):
        if item.get('quality') == "480p":
            return Quality.SDTV
        elif item.get('quality') == "720p":
            return Quality.HDWEBDL
        elif item.get('quality') == "1080p":
            return Quality.FULLHDWEBDL
        else:
            return Quality.sceneQuality(item.get('title'), anime)

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():

            if mode != 'Episode':
                logger.log(u"" + self.name + " does not accept " + mode + " mode", logger.DEBUG)
                return results

            for search_string in search_params[mode]:

                searchURL = self.urls['show'] % (search_string['imdb_id'])
                logger.log(u"" + self.name + " search page URL: " + searchURL, logger.DEBUG)

                try:
                    parsedJSON = self.getURL(searchURL, json=True)
                except ValueError as e:
                    parsedJSON = None

                if not parsedJSON:
                    logger.log(u"" + self.name + " could not retrieve page URL:" + searchURL, logger.DEBUG)
                    return results

            try:
                for episode in parsedJSON['episodes']:
                    if int(episode.get('season')) == search_string.get('season') and \
                       int(episode.get('episode')) == search_string.get('episode'):

                        for quality in episode['torrents'].keys():
                            link = episode['torrents'][quality]['url']
                            title = re.search('&dn=(.*?)&', link).group(1)

                            item = {
                                'title': title,
                                'link': link,
                                'quality': quality
                            }

                            # re.search in case of PROPER|REPACK. In other cases
                            # add_string is empty, so condition is met.
                            if re.search(search_string.get('add_string'), title):
                                items[mode].append(item)

                        break

            except Exception, e:
                logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(),
                            logger.ERROR)

            results += items[mode]

        return results

    def findPropers(self, search_date=datetime.datetime.today()):

        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        if not sqlResults:
            return []

        for sqlshow in sqlResults:
            self.show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))

            if self.show:
                curEp = self.show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

                searchString = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')

                for item in self._doSearch(searchString[0]):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

class EZTVCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # Only poll EZTV every 5 minutes max
        self.minTime = 5

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = EZTVProvider()
