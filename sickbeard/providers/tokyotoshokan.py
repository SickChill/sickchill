# Author: Mr_Orange
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import traceback

import generic

from sickbeard import show_name_helpers
from sickbeard import logger
from sickbeard.common import Quality
from sickbeard import tvcache
from sickbeard import show_name_helpers
from sickbeard.bs4_parser import BS4Parser


class TokyoToshokanProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "TokyoToshokan")

        self.supportsBacklog = True
        self.public = True
        self.supportsAbsoluteNumbering = True
        self.anime_only = True
        self.enabled = False
        self.ratio = None

        self.cache = TokyoToshokanCache(self)

        self.urls = {'base_url': 'http://tokyotosho.info/'}
        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def seedRatio(self):
        return self.ratio

    def findSearchResults(self, show, episodes, search_mode, manualSearch=False, downCurQuality=False):
        return generic.TorrentProvider.findSearchResults(self, show, episodes, search_mode, manualSearch, downCurQuality)

    def _get_season_search_strings(self, ep_obj):
        return [x.replace('.', ' ') for x in show_name_helpers.makeSceneSeasonSearchString(self.show, ep_obj)]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        return [x.replace('.', ' ') for x in show_name_helpers.makeSceneSearchString(self.show, ep_obj)]

    def _doSearch(self, search_string, search_mode='eponly', epcount=0, age=0, epObj=None):
        #FIXME ADD MODE
        if self.show and not self.show.is_anime:
            return []

        logger.log(u"Search string: %s " % search_string, logger.DEBUG)

        params = {
            "terms": search_string.encode('utf-8'),
            "type": 1, # get anime types
        }

        searchURL = self.url + 'search.php?' + urllib.urlencode(params)
        logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG) 
        data = self.getURL(searchURL)

        if not data:
            return []

        results = []
        try:
            with BS4Parser(data, features=["html5lib", "permissive"]) as soup:
                torrent_table = soup.find('table', attrs={'class': 'listing'})
                torrent_rows = torrent_table.find_all('tr') if torrent_table else []
                if torrent_rows: 
                    if torrent_rows[0].find('td', attrs={'class': 'centertext'}):
                        a = 1
                    else:
                        a = 0

                    for top, bottom in zip(torrent_rows[a::2], torrent_rows[a::2]):
                        title = top.find('td', attrs={'class': 'desc-top'}).text
                        title.lstrip()
                        download_url = top.find('td', attrs={'class': 'desc-top'}).find('a')['href']
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

                        results.append(item)

        except Exception, e:
            logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

        #FIXME SORTING
        return results


class TokyoToshokanCache(tvcache.TVCache):
    def __init__(self, provider):
        tvcache.TVCache.__init__(self, provider)

        # only poll NyaaTorrents every 15 minutes max
        self.minTime = 15

    def _getRSSData(self):
        params = {
            "filter": '1',
        }

        url = self.provider.url + 'rss.php?' + urllib.urlencode(params)

        logger.log(u"Cache update URL: %s" % url, logger.DEBUG)

        return self.getRSSFeed(url)


provider = TokyoToshokanProvider()
