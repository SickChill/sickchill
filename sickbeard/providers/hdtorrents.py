# Author: Idan Gutman
# Modified by jkaberg, https://github.com/jkaberg for SceneAccess
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

import re
import sickbeard
import generic
import urllib
from sickbeard.common import Quality
from sickbeard import logger
from sickbeard import tvcache
from sickbeard import db
from sickbeard import classes
from sickbeard import helpers
from sickbeard import show_name_helpers
from sickrage.helper.exceptions import AuthException
import requests
from BeautifulSoup import BeautifulSoup as soup
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from datetime import datetime
import traceback

class HDTorrentsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "HDTorrents")

        self.supportsBacklog = True
        self.public = False

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'https://hd-torrents.org',
                     'login': 'https://hd-torrents.org/login.php',
                     'search': 'https://hd-torrents.org/torrents.php?search=%s&active=1&options=0%s',
                     'rss': 'https://hd-torrents.org/torrents.php?search=&active=1&options=0%s',
                     'home': 'https://hd-torrents.org/%s'
        }

        self.url = self.urls['base_url']

        self.cache = HDTorrentsCache(self)

        self.categories = "&category[]=59&category[]=60&category[]=30&category[]=38"

    def isEnabled(self):
        return self.enabled

    def _checkAuth(self):

        if not self.username or not self.password:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)

        return True

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'uid': self.username,
                        'pwd': self.password,
                        'submit': 'Confirm'}

        response = self.getURL(self.urls['login'],  post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('You need cookies enabled to log in.', response):
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode != 'RSS':
                    searchURL = self.urls['search'] % (urllib.quote_plus(search_string.replace('.', ' ')), self.categories)
                else:
                    searchURL = self.urls['rss'] % self.categories

                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                if mode != 'RSS':
                    logger.log(u"Search string: %s" %  search_string, logger.DEBUG)

                data = self.getURL(searchURL)
                if not data or 'please try later' in data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                html = soup(data)
                if not html:
                    logger.log("No html data parsed from provider", logger.DEBUG)
                    continue

                empty = html.find('No torrents here')
                if empty:
                    logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                tables = html.find('table', attrs={'class': 'mainblockcontenttt'})
                if not tables:
                    logger.log(u"Could not find table of torrents mainblockcontenttt", logger.ERROR)
                    continue

                torrents = tables.findChildren('tr')
                if not torrents:
                    continue

                # Skip column headers
                for result in torrents[1:]:
                    try:
                        cells = result.findChildren('td', attrs={'class': re.compile(r'(green|yellow|red|mainblockcontent)')})
                        if not cells:
                            continue

                        title = download_url = seeders = leechers = None
                        size = 0
                        for cell in cells:
                            try:
                                if None is title and cell.get('title') and cell.get('title') in 'Download':
                                    title = re.search('f=(.*).torrent', cell.a['href']).group(1).replace('+', '.')
                                    download_url = self.urls['home'] % cell.a['href']
                                if None is seeders and cell.get('class')[0] and cell.get('class')[0] in 'green' 'yellow' 'red':
                                    seeders = int(cell.text)
                                    if not seeders:
                                        seeders = 1
                                elif None is leechers and cell.get('class')[0] and cell.get('class')[0] in 'green' 'yellow' 'red':
                                    leechers = int(cell.text)
                                    if not leechers:
                                        seeders = 0

                                # Need size for failed downloads handling
                                if re.match(r'[0-9]+,?\.?[0-9]* [KkMmGg]+[Bb]+', cells[7].text):
                                    size = self._convertSize(cells[7].text)
                                    if not size:
                                        size = -1

                            except:
                                logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

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
                        continue

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def findPropers(self, search_date=datetime.today()):

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
            self.show = curshow = helpers.findCertainShow(sickbeard.showList, int(sqlshow["showid"]))
            if not self.show: continue
            curEp = curshow.getEpisode(int(sqlshow["season"]), int(sqlshow["episode"]))

            proper_searchString = self._get_episode_search_strings(curEp, add_string='PROPER')

            for item in self._doSearch(proper_searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.today(), self.show))

            repack_searchString = self._get_episode_search_strings(curEp, add_string='REPACK')

            for item in self._doSearch(repack_searchString[0]):
                title, url = self._get_title_and_url(item)
                results.append(classes.Proper(title, url, datetime.today(), self.show))

        return results

    def seedRatio(self):
        return self.ratio

    def _convertSize(self, size):
        size, modifier = size.split(' ')
        size = float(size)
        if modifier in 'KB':
            size = size * 1024
        elif modifier in 'MB':
            size = size * 1024**2
        elif modifier in 'GB':
            size = size * 1024**3
        elif modifier in 'TB':
            size = size * 1024**4
        return size

class HDTorrentsCache(tvcache.TVCache):
    def __init__(self, provider):

        tvcache.TVCache.__init__(self, provider)

        # only poll HDTorrents every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}

provider = HDTorrentsProvider()
