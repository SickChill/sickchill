# -*- coding: latin-1 -*-
# Author: adaur <adaur.underground@gmail.com>
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
import cookielib
import urllib
import requests

from sickbeard import logger
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser


class XthorProvider(generic.TorrentProvider):

    def __init__(self):

        generic.TorrentProvider.__init__(self, "Xthor")

        self.supportsBacklog = True

        self.cj = cookielib.CookieJar()

        self.url = "https://xthor.bz"
        self.urlsearch = "https://xthor.bz/browse.php?search=\"%s\"%s"
        self.categories = "&searchin=title&incldead=0"

        self.username = None
        self.password = None
        self.ratio = None

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submitme': 'X'}

        response = self.getURL(self.url + '/takelogin.php', post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('donate.php', response):
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
                    resultsTable = html.find("table", {"class" : "table2 table-bordered2"})
                    if resultsTable:
                        rows = resultsTable.findAll("tr")
                        for row in rows:
                            link = row.find("a", href=re.compile("details.php"))
                            if link:
                                title = link.text
                                download_url = self.url + '/' + row.find("a", href=re.compile("download.php"))['href']
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

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio

provider = XthorProvider()
