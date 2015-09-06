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
import urllib
import re
import datetime

import sickbeard
import generic

from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard import db
from sickbeard import classes
from sickbeard.show_name_helpers import allPossibleShowNames, sanitizeSceneName
from unidecode import unidecode


class KATProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "KickAssTorrents")

        self.supportsBacklog = True

        self.enabled = False
        self.confirmed = False
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = KATCache(self)

        self.urls = {'base_url': 'https://kat.cr/'}

        self.url = self.urls['base_url']

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'kat.png'

    def _get_season_search_strings(self, ep_obj):
        search_string = {'Season': []}

        for show_name in set(allPossibleShowNames(self.show)):
            ep_string = sanitizeSceneName(show_name) + ' '
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string += str(ep_obj.airdate).split('-')[0]
                search_string['Season'].append(ep_string)
            elif ep_obj.show.anime:
                ep_string += "%02d" % ep_obj.scene_absolute_number
                search_string['Season'].append(ep_string)
            else:
                ep_string = '%s S%02d -S%02dE category:tv' % (sanitizeSceneName(show_name), ep_obj.scene_season, ep_obj.scene_season) #1) showName SXX -SXXE
                search_string['Season'].append(ep_string)
                ep_string = '%s "Season %d" -Ep* category:tv' % (sanitizeSceneName(show_name), ep_obj.scene_season) # 2) showName "Season X"
                search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        search_string = {'Episode': []}

        for show_name in set(allPossibleShowNames(self.show)):
            ep_string = sanitizeSceneName(show_name) + ' '
            if self.show.air_by_date:
                ep_string += str(ep_obj.airdate).replace('-', ' ')
            elif self.show.sports:
                ep_string += str(ep_obj.airdate).replace('-', ' ') + '|' + ep_obj.airdate.strftime('%b')
            elif self.show.anime:
                ep_string += "%02d" % ep_obj.scene_absolute_number
            else:
                ep_string += sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode} + '|' + \
                             sickbeard.config.naming_ep_type[0] % {'seasonnumber': ep_obj.scene_season,
                                                                   'episodenumber': ep_obj.scene_episode} + ' category:tv'
            if add_string:
                ep_string += ' ' + add_string

            search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _get_size(self, item):
        title, url, id, seeders, leechers, size, pubdate = item
        return size or -1

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):
        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            for search_string in search_params[mode]:
                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                if mode != 'RSS':
                    searchURL = self.url + 'usearch/%s/?field=seeders&sorder=desc&rss=1' % urllib.quote_plus(search_string)
                else:
                    searchURL = self.url + 'tv/?field=time_add&sorder=desc&rss=1'

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                try:
                    entries = self.cache.getRSSFeed(searchURL)['entries']
                    for item in entries or []:
                        try:
                            link = item['link']
                            id = item['guid']
                            title = item['title']
                            url = item['torrent_magneturi']
                            verified = bool(int(item['torrent_verified']) or 0)
                            seeders = int(item['torrent_seeds'])
                            leechers = int(item['torrent_peers'])
                            size = int(item['torrent_contentlength'])
                        except (AttributeError, TypeError, KeyError):
                            continue

                        if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                            continue

                        if self.confirmed and not verified:
                            logger.log(u"KAT Provider found result " + title + " but that doesn't seem like a verified result so I'm ignoring it", logger.DEBUG)
                            continue

                        if not title or not url:
                            continue

                        try:
                            pubdate = datetime.datetime(*item['published_parsed'][0:6])
                        except AttributeError:
                            try:
                                pubdate = datetime.datetime(*item['updated_parsed'][0:6])
                            except AttributeError:
                                try:
                                    pubdate = datetime.datetime(*item['created_parsed'][0:6])
                                except AttributeError:
                                    try:
                                        pubdate = datetime.datetime(*item['date'][0:6])
                                    except AttributeError:
                                        pubdate = datetime.datetime.today()

                        item = title, url, id, seeders, leechers, size, pubdate

                        items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed to parsing " + self.name + " Traceback: " + traceback.format_exc(),
                               logger.ERROR)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):
        title, url, id, seeders, leechers, size, pubdate = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

    def findPropers(self, search_date=datetime.datetime.today()):
        results = []

        myDB = db.DBConnection()
        sqlResults = myDB.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate, s.indexer FROM tv_episodes AS e' +
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
                    pubdate = item[6]

                    results.append(classes.Proper(title, url, pubdate, self.show))

        return results

    def seedRatio(self):
        return self.ratio


class KATCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll KickAss every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['rss']}
        return {'entries': self.provider._doSearch(search_params)}

provider = KATProvider()
