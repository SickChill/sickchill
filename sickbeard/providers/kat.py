# coding=utf-8
# Author: Mr_Orange <mr_orange@hotmail.it>
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

from __future__ import with_statement

import traceback
import re
import datetime
import xmltodict
from urllib import urlencode

import sickbeard
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import db
from sickbeard import classes
from sickbeard.common import Quality
from sickbeard.common import USER_AGENT
from sickbeard.providers import generic
from sickbeard.show_name_helpers import allPossibleShowNames, sanitizeSceneName

class KATProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "KickAssTorrents")

        self.supportsBacklog = True
        self.public = True

        self.enabled = False
        self.confirmed = True
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = KATCache(self)

        self.urls = {
            'base_url': 'https://kat.cr/',
            'search': 'https://kat.cr/usearch/',
            'rss': 'https://kat.cr/tv/',
        }

        self.url = self.urls['base_url']
        self.headers.update({'User-Agent': USER_AGENT})

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

    def isEnabled(self):
        return self.enabled

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                self.search_params.update({'q': search_string, 'field': ('seeders', 'time_add')[mode == 'RSS']})

                if mode != 'RSS':
                    logger.log(u"Search string: %s" % search_string, logger.DEBUG)

                try:
                    searchURL = self.urls[('search', 'rss')[mode == 'RSS']] + '?' + urlencode(self.search_params)
                    logger.log(u"Search URL: %s" % searchURL, logger.DEBUG) 
                    data = self.getURL(searchURL)
                    #data = self.getURL(self.urls[('search', 'rss')[mode == 'RSS']], params=self.search_params)
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
                        try:
                            title = item['title']

                            # Use the torcache link kat provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            download_url = item['enclosure']['@url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'torcache' not in download_url:
                                download_url = item['torrent:magnetURI']

                            seeders = int(item['torrent:seeds'])
                            leechers = int(item['torrent:peers'])
                            verified = bool(int(item['torrent:verified']) or 0)
                            size = int(item['torrent:contentLength'])

                            info_hash = item['torrent:infoHash']
                            #link = item['link']

                        except (AttributeError, TypeError, KeyError):
                            continue

                        try:
                            pubdate = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0000')
                        except Exception:
                            pubdate = datetime.datetime.today()

                        if not all([title, download_url]):
                            continue

                        #Filter unseeded torrent
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != 'RSS':
                                logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        if self.confirmed and not verified and mode != 'RSS':
                            logger.log(u"Found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                            continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

                except Exception:
                    logger.log(u"Failed parsing provider. Traceback: %r" % traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def findPropers(self, search_date=datetime.datetime.today()-datetime.timedelta(days=1)):
        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate, s.indexer FROM tv_episodes AS e' +
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
                    pubdate = item[6]

                    results.append(classes.Proper(title, url, pubdate, show))

        return results

    def seedRatio(self):
        return self.ratio


class KATCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = KATProvider()
