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

import sickbeard
from sickbeard.providers import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import db
from sickbeard import classes
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

        self.search_params = {
            'q': '',
            'field': 'seeders',
            'sorder': 'desc',
            'rss': 1,
            'category': 'tv'
        }

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'kat.png'

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}

        for show_name in set(allPossibleShowNames(ep_obj.show)):
            ep_string = sanitizeSceneName(show_name) + ' '
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string += str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string += "%02d" % ep_obj.scene_absolute_number
            else:
                ep_string = '%s S%02d -S%02dE category:tv' % (sanitizeSceneName(show_name), ep_obj.scene_season, ep_obj.scene_season) #1) showName SXX -SXXE
                search_string['Season'].append(ep_string)
                ep_string = '%s "Season %d" -Ep* category:tv' % (sanitizeSceneName(show_name), ep_obj.scene_season) # 2) showName "Season X"

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        search_string = {'Episode': []}

        for show_name in set(allPossibleShowNames(ep_obj.show)):
            ep_string = sanitizeSceneName(show_name) + ' '
            if ep_obj.show.air_by_date:
                ep_string += str(ep_obj.airdate).replace('-', ' ')
            elif ep_obj.show.sports:
                ep_string += str(ep_obj.airdate).replace('-', ' ') + '|' + ep_obj.airdate.strftime('%b')
            elif ep_obj.show.anime:
                ep_string += "%02d" % ep_obj.scene_absolute_number
            else:
                ep_string += sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode} + '|' + \
                             sickbeard.config.naming_ep_type[0] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode}
            if add_string:
                ep_string += ' ' + add_string

            search_string['Episode'].append(re.sub(r'\s+', ' ', ep_string.strip()))

        return [search_string]

    def _get_size(self, item):
        #pylint: disable=W0612
        title, url, info_hash, seeders, leechers, size, pubdate = item
        return size or -1

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_strings.keys():
            for search_string in search_strings[mode]:
                self.search_params.update({'q': search_string, 'field': ('seeders', 'time_add')[mode == 'RSS']})
                logger.log(u"Search string: %s" % unicode(self.search_params), logger.DEBUG)

                try:
                    data = self.getURL(self.urls[('search', 'rss')[mode == 'RSS']], params=self.search_params)
                    if not data:
                        continue

                    entries = xmltodict.parse(data)
                    if not all([entries, 'rss' in entries, 'channel' in entries['rss'], 'item' in entries['rss']['channel']]):
                        continue

                    for item in entries['rss']['channel']['item']:
                        try:
                            title = item['title']

                            # Use the torcache link kat provides,
                            # unless it is not torcache or we are not using blackhole
                            # because we want to use magnets if connecting direct to client
                            # so that proxies work.
                            url = item['enclosure']['@url']
                            if sickbeard.TORRENT_METHOD != "blackhole" or 'torcache' not in url:
                                url = item['torrent:magnetURI']

                            seeders = int(item['torrent:seeds'])
                            leechers = int(item['torrent:peers'])
                            verified = bool(int(item['torrent:verified']) or 0)
                            size = int(item['torrent:contentLength'])

                            info_hash = item['torrent:infoHash']
                            #link = item['link']

                        except (AttributeError, TypeError, KeyError):
                            continue

                        # Dont let RSS add items with no seeders either -.-
                        if not seeders or seeders < self.minseed or leechers < self.minleech:
                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                            continue

                        if self.confirmed and not verified:
                            logger.log(u"KAT Provider found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                            continue

                        if not title or not url:
                            continue

                        try:
                            pubdate = datetime.datetime.strptime(item['pubDate'], '%a, %d %b %Y %H:%M:%S +0000')
                        except Exception:
                            pubdate = datetime.datetime.today()

                        item = title, url, info_hash, seeders, leechers, size, pubdate

                        items[mode].append(item)

                except Exception:
                    logger.log(u"Failed to parsing " + self.name + " Traceback: " + traceback.format_exc(),
                               logger.WARNING)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):
        #pylint: disable=W0612
        title, url, info_hash, seeders, leechers, size, pubdate = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

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

                for item in self._doSearch(searchStrings):
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
