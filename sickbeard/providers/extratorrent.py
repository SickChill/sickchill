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
from sickbeard.common import USER_AGENT


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
        self.headers.update({'User-Agent': USER_AGENT})
        self.search_params = {'cid': 8}

    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                try:
                    self.search_params.update({'type': ('search', 'rss')[mode == 'RSS'], 'search': search_string.strip()})
                    data = self.getURL(self.urls['rss'], params=self.search_params)
                    if not data:
                        logger.log("No data returned from provider", logger.DEBUG)
                        continue

                    try:
                        data = xmltodict.parse(data)
                    except ExpatError as e:
                        logger.log(u"Failed parsing provider. Traceback: %r\n%r" % (traceback.format_exc(), data), logger.ERROR)
                        continue

                    if not all([data, 'rss' in data, 'channel' in data['rss'], 'item' in data['rss']['channel']]):
                        logger.log(u"Malformed rss returned, skipping", logger.DEBUG)
                        continue

                    # https://github.com/martinblech/xmltodict/issues/111
                    entries = data['rss']['channel']['item']
                    entries = entries if isinstance(entries, list) else [entries]

                    for item in entries:
                        title = item['title']
                        info_hash = item['info_hash']
                        size = int(item['size'])
                        seeders = helpers.tryInt(item['seeders'],0)
                        leechers = helpers.tryInt(item['leechers'],0)
                        download_url = item['enclosure']['@url'] if 'enclosure' in item else self._magnet_from_details(item['link'])

                        if not all([title, download_url]):
                            continue

                            #Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

                except (AttributeError, TypeError, KeyError, ValueError):
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _magnet_from_details(self, link):
        details = self.getURL(link)
        if not details:
            return ''

        match = re.search(r'href="(magnet.*?)"', details)
        if not match:
            return ''

        return match.group(1)

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
                for item in self._doSearch(searchStrings[0]):
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
