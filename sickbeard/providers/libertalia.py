# -*- coding: latin-1 -*-
# Authors: Raver2046
#          adaur
# based on tpi.py
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
import requests
import cookielib
import urllib

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser

class LibertaliaProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Libertalia")

        self.supportsBacklog = True

        self.cj = cookielib.CookieJar()

        self.url = "https://libertalia.me"
        self.urlsearch = "https://libertalia.me/torrents.php?name=%s%s"

        self.categories = "&cat%5B%5D=9&cat%5B%5D=10"

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = LibertaliaCache(self)

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password}

        response = self.getURL(self.url + '/login.php', post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('upload.php', response):
            return True
        else:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True


    def _doSearch(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urlsearch % (urllib.quote(search_string), self.categories)
                logger.log(u"Search URL: %s" %  searchURL, logger.DEBUG)
                data = self.getURL(searchURL)
                if not data:
                    continue

                with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                    resultsTable = html.find("table", {"class" : "torrent_table"})
                    if resultsTable:
                        rows = resultsTable.findAll("tr", {"class" : re.compile("torrent_row(.*)?")})
                        for row in rows:

                            # bypass first row because title only
                            columns = row.find('td', {"class" : "torrent_name"})
                            # isvfclass = row.find('td', {"class" : "sprite-vf"})
                            # isvostfrclass = row.find('td', {"class" : "sprite-vostfr"})
                            link = columns.find("a", href=re.compile("torrents"))
                            if link:
                                title = link.text
                                # recherched = searchURL.replace(".", "(.*)").replace(" ", "(.*)").replace("'", "(.*)")
                                download_url = row.find("a", href=re.compile("torrent_pass"))['href']
                                # FIXME
                                size = -1
                                seeders = 1
                                leechers = 0

                                if not all([title, download_url]):
                                    continue

                                # Filter unseeded torrent
                                # if seeders < self.minseed or leechers < self.minleech:
                                #    if mode is not 'RSS':
                                #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                #    continue

                                item = title, download_url, size, seeders, leechers
                                if mode is not 'RSS':
                                    logger.log(u"Found result: %s " % title, logger.DEBUG)

                                items[mode].append(item)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class LibertaliaCache(tvcache.TVCache):
    def __init__(self, provider_obj):

        tvcache.TVCache.__init__(self, provider_obj)

        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}

provider = LibertaliaProvider()
