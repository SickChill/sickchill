# Author: Seamus Wassman
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

# This file was adapted for MoreThanTV from the freshontv scraper by
# Sparhawk76, this is my first foray into python, so there most likely
# are some mistakes or things I could have done better.

import re
import traceback
import datetime
import sickbeard
import generic
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickbeard.exceptions import ex, AuthException
import requests
from sickbeard.bs4_parser import BS4Parser
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName


class MoreThanTVProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "MoreThanTV")

        self.supportsBacklog = True

        self.enabled = False
        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        self.cache = MoreThanTVCache(self)

        self.urls = {'base_url': 'https://www.morethan.tv/',
                'login': 'https://www.morethan.tv/login.php',
                'detail': 'https://www.morethan.tv/torrents.php?id=%s',
                'search': 'https://www.morethan.tv/torrents.php?tags_type=1&order_by=time&order_way=desc&action=basic&searchsubmit=1&searchstr=%s',
                'download': 'https://www.morethan.tv/torrents.php?action=download&id=%s',
                }

        self.url = self.urls['base_url']

        self.cookies = None

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'morethantv.png'

    def getQuality(self, item, anime=False):

        quality = Quality.sceneQuality(item[0], anime)
        return quality

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):
        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        if self._uid and self._hash:
            requests.utils.add_dict_to_cookiejar(self.session.cookies, self.cookies)
        else:
            login_params = {'username': self.username,
                            'password': self.password,
                            'login': 'submit'
            }

            response = self.getURL(self.urls['login'],  post_data=login_params, timeout=30)
            if not response:
                logger.log(u'Unable to connect to ' + self.name + ' provider.', logger.ERROR)
                return False

            if re.search('Your username or password was incorrect.', response):
                logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
                return False

            return True

    def _get_season_search_strings(self, ep_obj):

        search_string = {'Season': []}
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + '.' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + '.' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + '.S%02d*' % int(ep_obj.scene_season)  #1) showName SXX

            search_string['Season'].append(re.sub('\.', '+', ep_string))

        return [search_string]

    def _get_episode_search_strings(self, ep_obj, add_string=''):

        search_string = {'Episode': []}

        if not ep_obj:
            return []

        if self.show.air_by_date:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
                search_string['Episode'].append(ep_string)
        elif self.show.sports:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
                search_string['Episode'].append(ep_string)
        elif self.show.anime:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
                search_string['Episode'].append(ep_string)
        else:
            for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode} + ' %s' % add_string

                search_string['Episode'].append(re.sub('\.', '+', ep_string))

        return [search_string]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '3' if self.freeleech else '0'

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            for search_string in search_params[mode]:

                if isinstance(search_string, unicode):
                    search_string = unidecode(search_string)

                searchURL = self.urls['search'] % (search_string)

                logger.log(u"Search string: " + searchURL, logger.DEBUG)

                # returns top 15 results by default, expandable in user profile to 100
                data = self.getURL(searchURL)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        torrent_table = html.find('table', attrs={'class': 'torrent_table'})
                        torrent_rows = torrent_table.findChildren('tr') if torrent_table else []

                        #Continue only if one Release is found
                        if len(torrent_rows) < 2:
                            logger.log(u"The Data returned from " + self.name + " do not contains any torrent",
                                       logger.DEBUG)
                            continue

                        # skip colheader
                        for result in torrent_rows[1:]:
                            cells = result.findChildren('td')

                            link = cells[1].find('a', attrs = {'title': 'Download'})

                            link_str = str(link['href'])

                            logger.log(u"link=" + link_str, logger.DEBUG)

                            #skip if torrent has been nuked due to poor quality
                            if cells[1].find('img', alt='Nuked') != None:
                                continue
                            torrent_id_long = link['href'].replace('torrents.php?action=download&id=', '')
                            torrent_id = torrent_id_long.split('&', 1)[0]


                            try:
                                if link.has_key('title'):
                                    title = cells[1].find('a', {'title': 'View torrent'}).contents[0].strip()
                                else:
                                    title = link.contents[0]
                                download_url = self.urls['download'] % (torrent_id_long)

                                seeders = cells[6].contents[0]

                                leechers = cells[7].contents[0]

                            except (AttributeError, TypeError):
                                continue


                            #Filter unseeded torrent
                            if mode != 'RSS' and (seeders < self.minseed or leechers < self.minleech):
                                continue

                            if not title or not download_url:
                                continue

# Debug
#                            logger.log(u"title = " + title + ", download_url = " + download_url + ", torrent_id = " + torrent_id + ", seeders = " + seeders + ", leechers = " + leechers, logger.DEBUG)


                            item = title, download_url, torrent_id, seeders, leechers
                            logger.log(u"Found result: " + title + "(" + searchURL + ")", logger.DEBUG)

                            items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing " + self.name + " Traceback: " + traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def _get_title_and_url(self, item):

        title, url, id, seeders, leechers = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = str(url).replace('&amp;', '&')

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
                    results.append(classes.Proper(title, url, datetime.datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio


class MoreThanTVCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # poll delay in minutes
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = MoreThanTVProvider()
