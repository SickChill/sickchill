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
from sickbeard.exceptions import ex, AuthException
import requests
from BeautifulSoup import BeautifulSoup as soup
from unidecode import unidecode
from sickbeard.helpers import sanitizeSceneName
from datetime import datetime

class HDTorrentsProvider(generic.TorrentProvider):
    def __init__(self):

        generic.TorrentProvider.__init__(self, "HDTorrents")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.urls = {'base_url': 'https://hd-torrents.org',
                     'login': 'https://hd-torrents.org/login.php',
                     'search': 'https://hd-torrents.org/torrents.php?search=%s&active=1&options=0%s',
                     'home': 'https://hd-torrents.org/%s'
        }

        self.url = self.urls['base_url']

        self.cache = HDTorrentsCache(self)

        self.categories = "&category[]=59&category[]=60&category[]=30&category[]=38"

    def isEnabled(self):
        return self.enabled

    def imageName(self):
        return 'hdtorrents.png'

    def _checkAuth(self):

        if not self.username or not self.password:
            raise AuthException("Your authentication credentials for " + self.name + " are missing, check your config.")

        return True

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'uid': self.username,
                        'pwd': self.password,
                        'submit': 'Confirm'}

        response = self.getURL(self.urls['login'],  post_data=login_params, timeout=30)
        if not response:
            logger.log(u'Unable to connect to ' + self.name + ' provider.', logger.ERROR)
            return False

        if re.search('You need cookies enabled to log in.', response):
            logger.log(u'Invalid username or password for ' + self.name + ' Check your settings', logger.ERROR)
            return False

        return True

    def _get_season_search_strings(self, ep_obj):
        if not ep_obj:
            return []

        search_strings = []
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if ep_obj.show.air_by_date or ep_obj.show.sports:
                ep_string = show_name + ' ' + str(ep_obj.airdate).split('-')[0]
            elif ep_obj.show.anime:
                ep_string = show_name + ' ' + "%d" % ep_obj.scene_absolute_number
            else:
                ep_string = show_name + ' S%02d' % ep_obj.scene_season

            search_strings.append(ep_string)

        return [search_strings]

    def _get_episode_search_strings(self, ep_obj, add_string=''):
        if not ep_obj:
            return []

        search_strings = []
        for show_name in set(show_name_helpers.allPossibleShowNames(self.show)):
            if self.show.air_by_date:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|')
            elif self.show.sports:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            str(ep_obj.airdate).replace('-', '|') + '|' + \
                            ep_obj.airdate.strftime('%b')
            elif self.show.anime:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            "%i" % int(ep_obj.scene_absolute_number)
            else:
                ep_string = sanitizeSceneName(show_name) + ' ' + \
                            sickbeard.config.naming_ep_type[2] % {'seasonnumber': ep_obj.scene_season,
                                                                  'episodenumber': ep_obj.scene_episode}
            if add_string:
                ep_string += ' %s' % add_string

            search_strings.append(ep_string)

        return [search_strings]

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []

        if not self._doLogin():
            return results

        for search_string in search_params if search_params else '':
            if isinstance(search_string, unicode):
                search_string = unidecode(search_string)


            searchURL = self.urls['search'] % (urllib.quote_plus(search_string.replace('.', ' ')), self.categories)
            logger.log(u"Search string: " + searchURL, logger.DEBUG)
            data = self.getURL(searchURL)
            if not data:
                logger.log(u'No grabs for you', logger.DEBUG)
                continue

            html = soup(data)
            if not html:
                continue

            empty = html.find('No torrents here')
            if empty:
                logger.log(u"Could not find any torrents", logger.ERROR)
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

                    title = url = seeders = leechers = None
                    size = 0
                    for cell in cells:
                        try:
                            if None is title and cell.get('title') and cell.get('title') in 'Download':
                                title = re.search('f=(.*).torrent', cell.a['href']).group(1).replace('+', '.')
                                url = self.urls['home'] % cell.a['href']
                            if None is seeders and cell.get('class')[0] and cell.get('class')[0] in 'green' 'yellow' 'red':
                                seeders = int(cell.text)
                            elif None is leechers and cell.get('class')[0] and cell.get('class')[0] in 'green' 'yellow' 'red':
                                leechers = int(cell.text)
    
                            # Skip torrents released before the episode aired (fakes)
                            if re.match('..:..:..  ..:..:....', cells[6].text):
                                if (datetime.strptime(cells[6].text, '%H:%M:%S  %m/%d/%Y') -
                                    datetime.combine(epObj.airdate, datetime.min.time())).days < 0:
                                    continue
        
                            # Need size for failed downloads handling
                            if re.match('[0-9]+,?\.?[0-9]* [KkMmGg]+[Bb]+', cells[7].text):
                                size = self._convertSize(cells[7].text)
        
                            if not title or not url or not seeders or leechers is None or not size or \
                                    seeders < self.minseed or leechers < self.minleech:
                                continue
            
                            item = title, url, seeders, leechers, size
                            logger.log(u"Found result: " + title + " (" + searchURL + ")", logger.DEBUG)
            
                            results.append(item)

                        except:
                            raise

                except (AttributeError, TypeError, KeyError, ValueError):
                    continue

        results.sort(key=lambda tup: tup[3], reverse=True)
        return results

    def _get_title_and_url(self, item):

        title, url, seeders, leechers, size = item

        if title:
            title = self._clean_title_from_provider(title)

        if url:
            url = str(url).replace('&amp;', '&')

        return (title, url)

    def _get_size(self, item):

        title, url, seeders, leechers, size = item

        return size

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
        self.minTime = 20

    def _getRSSData(self):
        search_params = []
        return {'entries': self.provider._doSearch(search_params)}


provider = HDTorrentsProvider()
