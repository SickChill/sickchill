# Author: matigonkas
# URL: https://github.com/SiCKRAGETV/sickrage
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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import generic

from sickbeard import logger
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard import db
from sickbeard.common import WANTED
from sickbeard.config import naming_ep_type
from sickbeard.helpers import sanitizeSceneName

class STRIKEProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "Strike")

        self.supportsBacklog = True
        self.public = True
        self.url = 'https://getstrike.net/'

        self.cache = StrikeCache(self)
        self.minseed, self.minleech = 2 * [None]
		
    def isEnabled(self):
        return self.enabled


    def imageName(self):
        return 'getstrike.png'


    def _get_airbydate_season_range(self, season):
        if season == None:
            return ()
        year, month = map(int, season.split('-'))
        min_date = datetime.date(year, month, 1)
        if month == 12:
            max_date = datetime.date(year, month, 31)
        else:
            max_date = datetime.date(year, month+1, 1) -  datetime.timedelta(days=1)
        return (min_date, max_date)


    def _get_season_search_strings(self, show, season=None):
        search_string = []

        if not (show and season):
            return []

        myDB = db.DBConnection()

        if show.air_by_date:
            (min_date, max_date) = self._get_airbydate_season_range(season)
            sqlResults = myDB.select("SELECT DISTINCT airdate FROM tv_episodes WHERE showid = ? AND airdate >= ? AND airdate <= ? AND status = ?", [show.tvdbid,  min_date.toordinal(), max_date.toordinal(), WANTED])
        else:
            sqlResults = myDB.select("SELECT DISTINCT season FROM tv_episodes WHERE showid = ? AND season = ? AND status = ?", [show.tvdbid, season, WANTED])

        for sqlEp in sqlResults:
            for show_name in set(show_name_helpers.allPossibleShowNames(show)):
                if show.air_by_date:
                    ep_string = sanitizeSceneName(show_name) +' '+ str(datetime.date.fromordinal(sqlEp["airdate"])).replace('-', '.')
                    search_string.append(ep_string)
                else:
                    ep_string = sanitizeSceneName(show_name) + ' S%02d' % sqlEp["season"]
                    search_string.append(ep_string)

        return search_string


    def _get_episode_search_strings(self, ep_obj, add_string=''):

        if not ep_obj:
            return []

        search_string = []

        for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
            ep_string = sanitizeSceneName(show_name)
            if ep_obj.show.air_by_date:
                ep_string += ' ' + str(ep_obj.airdate).replace('-', '.')
            else:
                ep_string += ' ' + naming_ep_type[2] % {'seasonnumber': ep_obj.season, 'episodenumber': ep_obj.episode}

            if len(add_string):
                ep_string += ' %s' % add_string

            search_string.append(ep_string)

        return search_string


    def _get_title_and_url(self, item):
        title, url, size = item
        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)


    def _get_size(self, item):
        title, url, size = item
        logger.log(u'Size: %s' % size, logger.DEBUG)

        return size


    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        logger.log("Performing Search: {0}".format(search_params))

        searchUrl = self.url + "api/v2/torrents/search/?category=TV&phrase=" + search_params

        jdata = self.getURL(searchUrl, json=True)
        if not jdata:
            logger.log("No data returned to be parsed!!!")
            return []

        logger.log("URL to be parsed: " + searchUrl, logger.DEBUG)

        results = []

        for item in jdata['torrents']:
            seeders = ('seeds' in item and item['seeds']) or 0
            leechers = ('leeches' in item and item['leeches']) or 0
            name = ('torrent_title' in item and item['torrent_title']) or ''
            if seeders < self.minseed or leechers < self.minleech:
                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(name, seeders, leechers), logger.DEBUG)
                continue
            magnet = ('magnet_uri' in item and item['magnet_uri']) or ''
            if name and magnet:
                results.append((name, magnet, seeders))

        return results


class StrikeCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # set this 0 to suppress log line, since we aren't updating it anyways
        self.minTime = 0

    def _getRSSData(self):
        # no rss for getstrike.net afaik, also can't search with empty string
        return {'entries': {}}

provider = STRIKEProvider()
