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
import requests
import traceback

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser
from sickrage.helper.exceptions import AuthException


class MoreThanTVProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "MoreThanTV")

        self.supportsBacklog = True

        self._uid = None
        self._hash = None
        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None
        self.freeleech = False

        self.urls = {'base_url': 'https://www.morethan.tv/',
                     'login': 'https://www.morethan.tv/login.php',
                     'detail': 'https://www.morethan.tv/torrents.php?id=%s',
                     'search': 'https://www.morethan.tv/torrents.php?tags_type=1&order_by=time&order_way=desc&action=basic&searchsubmit=1&searchstr=%s',
                     'download': 'https://www.morethan.tv/torrents.php?action=download&id=%s'}

        self.url = self.urls['base_url']

        self.cookies = None

        self.proper_strings = ['PROPER', 'REPACK']

        self.cache = MoreThanTVCache(self)

    def isEnabled(self):
        return self.enabled

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
                            'login': 'submit'}

            response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
            if not response:
                logger.log(u"Unable to connect to provider", logger.WARNING)
                return False

            if re.search('Your username or password was incorrect.', response):
                logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
                return False

            return True

    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        freeleech = '3' if self.freeleech else '0'

        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urls['search'] % (search_string.replace('(', '').replace(')', ''))
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)

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
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        # skip colheader
                        for result in torrent_rows[1:]:
                            cells = result.findChildren('td')
                            link = cells[1].find('a', attrs={'title': 'Download'})

                            #skip if torrent has been nuked due to poor quality
                            if cells[1].find('img', alt='Nuked') != None:
                                continue

                            torrent_id_long = link['href'].replace('torrents.php?action=download&id=', '')

                            try:
                                if link.has_key('title'):
                                    title = cells[1].find('a', {'title': 'View torrent'}).contents[0].strip()
                                else:
                                    title = link.contents[0]
                                download_url = self.urls['download'] % (torrent_id_long)

                                seeders = cells[6].contents[0]

                                leechers = cells[7].contents[0]

                                #FIXME
                                size = -1

                            except (AttributeError, TypeError):
                                continue


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

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            #For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class MoreThanTVCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        # poll delay in minutes
        self.minTime = 20

    def _getRSSData(self):
        search_params = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_params)}

provider = MoreThanTVProvider()
