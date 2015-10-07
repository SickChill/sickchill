# coding=utf-8
# URL: http://code.google.com/p/sickbeard
# Originally written for SickGear
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib

import generic
from sickbeard import logger
from sickbeard import tvcache
from sickbeard.helpers import mapIndexersToShow
from sickrage.helper.exceptions import AuthException


class TitansOfTVProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, 'TitansOfTV')
        self.supportsBacklog = True
        self.public = False
        self.supportsAbsoluteNumbering = True
        self.api_key = None
        self.ratio = None
        self.cache = TitansOfTVCache(self)
        self.url = 'http://titansof.tv/api/torrents'
        self.download_url = 'http://titansof.tv/api/torrents/%s/download?apikey=%s'

    def isEnabled(self):
        return self.enabled

    def seedRatio(self):
        return self.ratio

    def _checkAuth(self):
        if not self.api_key:
            raise AuthException('Your authentication credentials for ' + self.name + ' are missing, check your config.')

        return True

    def _checkAuthFromData(self, data):

        if 'error' in data:
            logger.log(u"Invalid api key. Check your settings", logger.WARNING)

        return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
        #FIXME ADD MODE
        self._checkAuth()
        results = []
        params = {}
        self.headers.update({'X-Authorization': self.api_key})

        if search_params:
            params.update(search_params)

        searchURL = self.url + '?' + urllib.urlencode(params)
        logger.log(u"Search string: %s " % search_string, logger.DEBUG)
        logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG) 

        parsedJSON = self.getURL(searchURL, json=True)  # do search

        if not parsedJSON:
            logger.log("No data returned from provider", logger.DEBUG)
            return results

        if self._checkAuthFromData(parsedJSON):

            try:
                found_torrents = parsedJSON['results']
            except:
                found_torrents = {}

            for result in found_torrents:
                title = parsedJSON['release_name']
                id = parsedJSON['id']
                download_url = self.download_url % (id, self.api_key)
                #FIXME
                size = -1
                seeders = 1
                leechers = 0

                if not all([title, download_url]):
                    continue

                #Filter unseeded torrent
                #if seeders < self.minseed or leechers < self.minleech:
                #    if mode != 'RSS':
                #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                #    continue

                item = title, download_url, size, seeders, leechers

                logger.log(u"Found result: %s " % title, logger.DEBUG)
                results.append(result)

        #FIXME SORTING

        return results

    def _get_season_search_strings(self, ep_obj):
        search_params = {'limit': 100}

        search_params['season'] = 'Season %02d' % ep_obj.scene_season

        if ep_obj.show.indexer == 1:
            search_params['series_id'] = ep_obj.show.indexerid
        elif ep_obj.show.indexer == 2:
            tvdbid = mapIndexersToShow(ep_obj.show)[1]
            if tvdbid:
                search_params['series_id'] = tvdbid

        return [search_params]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        if not ep_obj:
            return [{}]

        search_params = {'limit': 100}

        # Do a general name search for the episode, formatted like SXXEYY
        search_params['episode'] = 'S%02dE%02d' % (ep_obj.scene_season, ep_obj.scene_episode)

        if ep_obj.show.indexer == 1:
            search_params['series_id'] = ep_obj.show.indexerid
        elif ep_obj.show.indexer == 2:
            tvdbid = mapIndexersToShow(ep_obj.show)[1]
            if tvdbid:
                search_params['series_id'] = tvdbid

        return [search_params]


class TitansOfTVCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # At least 10 minutes between queries
        self.minTime = 10

    def _getRSSData(self):
        search_params = {'limit': 100}
        return self.provider._doSearch(search_params)


provider = TitansOfTVProvider()
