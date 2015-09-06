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
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import re
import urllib
import datetime

import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import db
from sickbeard import classes
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import helpers
from sickbeard.show_name_helpers import allPossibleShowNames, sanitizeSceneName
from unidecode import unidecode


class ThePirateBayProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "ThePirateBay")

        self.supportsBacklog = True

        self.enabled = False
        self.ratio = None
        self.confirmed = False
        self.minseed = None
        self.minleech = None

        self.cache = ThePirateBayCache(self)

        self.urls = {'base_url': 'https://thepiratebay.gd/'}

        self.url = self.urls['base_url']

        self.searchurl = self.url + 'search/%s/0/7/200' # order by seed

        self.re_title_url = '/torrent/(?P<id>\d+)/(?P<title>.*?)//1".+?(?P<url>magnet.*?)//1".+?(?P<seeders>\d+)</td>.+?(?P<leechers>\d+)</td>'

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'thepiratebay.png'

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
                search_string['Season'].append(ep_string)
                ep_string = show_name + ' Season ' + str(ep_obj.airdate).split('-')[0]
                search_string['Season'].append(ep_string)
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%02d" % ep_obj.scene_absolute_number
                search_string['Season'].append(ep_string)
            else:
                ep_string = show_name + ' S%02d' % int(ep_obj.scene_season)
                search_string['Season'].append(ep_string)
                ep_string = show_name + ' Season ' + str(ep_obj.scene_season) + ' -Ep*'
                search_string['Season'].append(ep_string)

            search_string['Season'].append(ep_string)

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if self.show.air_by_date:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', ' ')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%02i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + '|' + \
                            sickbeard.config.naming_ep_type[0] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string
                search_string['Episode'].append(re.sub('\s+', ' ', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        for mode in search_params.keys():
            for search_string in search_params[mode]:
                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                if mode != 'RSS':
                    searchURL = self.searchurl % (urllib.quote(search_string))
                else:
                    searchURL = self.url + 'tv/latest/'

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data:
                    continue

                re_title_url = self.proxy._buildRE(self.re_title_url).replace('&amp;f=norefer', '')
                matches = re.compile(re_title_url, re.DOTALL).finditer(urllib.unquote(data))
                for torrent in matches:
                    title = torrent.group('title')
                    url = torrent.group('url')
                    id = int(torrent.group('id'))
                    seeders = int(torrent.group('seeders'))
                    leechers = int(torrent.group('leechers'))

                    #Filter unseeded torrent
                    if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                        continue

                    #Accept Torrent only from Good People for every Episode Search
                    if self.confirmed and re.search('(VIP|Trusted|Helper|Moderator)', torrent.group(0)) is None:
                        logger.log(u"ThePirateBay Provider found result " + torrent.group(
                            'title') + " but that doesn't seem like a trusted result so I'm ignoring it", logger.DEBUG)
                        continue

                    if not title or not url:
                        continue

                    item = title, url, id, seeders, leechers

                    items[mode].append(item)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, id, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = url.replace('&amp;', '&')

        return (title, url)

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
                    results.append(classes.Proper(title, url, search_date, self.show))

        return results

    def seedRatio(self):
        return self.ratio


class ThePirateBayCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll ThePirateBay every 10 minutes max
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['rss']}
        return {'entries': self.provider._doSearch(search_params)}

provider = ThePirateBayProvider()
