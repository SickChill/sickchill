# Author: duramato <matigonkas@outlook.com>
# Author: miigotu
# URL: https://github.com/SiCKRAGETV/sickrage
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

import re
import traceback
import datetime
import sickbeard
import xmltodict

from sickbeard.providers import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.helpers import sanitizeSceneName


class ExtraTorrentProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "ExtraTorrent")

        self.urls = {
            'index': 'http://extratorrent.cc',
            'rss': 'http://extratorrent.cc/rss.xml',
            }

        self.url = self.urls['index']

        self.supportsBacklog = True
        self.public = True
        self.enabled = False
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = ExtraTorrentCache(self)

        self.search_params = {'cid': 8}

    def isEnabled(self):
        return self.enabled

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)  #1) showName SXX

            search_string['Season'].append(ep_string.strip())

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_strings = {'Episode': []}

        if not ep_obj:
            return []

        for show_name in set(show_name_helpers.allPossibleShowNames(ep_obj.show)):
            if ep_obj.show.air_by_date:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                                str(ep_obj.airdate).replace('-', '|')
            elif ep_obj.show.sports:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                                str(ep_obj.airdate).replace('-', '|') + '|' + \
                                ep_obj.airdate.strftime('%b')
            elif ep_obj.show.anime:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                                "%i" % int(ep_obj.scene_absolute_number)
            else:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}

            if add_string:
                ep_string += ' %s' % add_string

            search_strings['Episode'].append(re.sub(r'\s+', ' ', ep_string))

        return [search_strings]


    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            for search_string in search_strings[mode]:
                try:
                    self.search_params.update({'type': ('search', 'rss')[mode == 'RSS'], 'search': search_string.strip()})
                    data = self.getURL(self.urls['rss'], params=self.search_params)
                    if not data:
                        continue

                    data = xmltodict.parse(data)
                    for item in data['rss']['channel']['item']:
                        title = item['title']
                        info_hash = item['info_hash']
                        url = item['enclosure']['@url']
                        size = int(item['enclosure']['@length'] or item['size'])
                        seeders = helpers.tryInt(item['seeders'],0)
                        leechers = helpers.tryInt(item['leechers'],0)

                        if not seeders or seeders < self.minseed or leechers < self.minleech:
                            continue

                        items[mode].append((title, url, seeders, leechers, size, info_hash))

                except Exception:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):
        #pylint: disable=W0612
        title, url, seeders, leechers, size, info_hash = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)


    def _get_size(self, item):
        #pylint: disable=W0612
        title, url, seeders, leechers, size, info_hash = item
        return size

    def findPropers(self, search_date=datetime.datetime.today()-datetime.timedelta(days=1)):
        results = []
        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate FROM tv_episodes AS e' +
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)' +
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND (e.status IN (' + ','.join([str(x) for x in Quality.DOWNLOADED]) + ')' +
            ' OR (e.status IN (' + ','.join([str(x) for x in Quality.SNATCHED]) + ')))'
        )

        for sqlshow in sqlResults or []:
            show = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if show:
                curEp = show.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))
                searchStrings = self._get_episode_search_strings(curEp, add_string='PROPER|REPACK')
                for item in self._doSearch(searchStrings):
                    title, url = self._get_title_and_url(item)
                    results.append(classes.Proper(title, url, datetime.datetime.today(), show))

        return results

    def seedRatio(self):
        return self.ratio


class ExtraTorrentCache(tvcache.TVCache):
    def __init__(self, _provider):

        tvcache.TVCache.__init__(self, _provider)

        self.minTime = 30

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = ExtraTorrentProvider()
