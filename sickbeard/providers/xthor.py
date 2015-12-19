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
from sickbeard.bs4_parser import BS4Parser
from sickrage.providers.TorrentProvider import TorrentProvider


class XthorProvider(TorrentProvider):

    def __init__(self):

        TorrentProvider.__init__(self, "Xthor")

        self.cj = cookielib.CookieJar()

        self.url = "https://xthor.bz"
        self.urlsearch = "https://xthor.bz/browse.php?search=\"%s\"%s"
        self.categories = "&searchin=title&incldead=0"

        self.username = None
        self.password = None
        self.ratio = None

    def login(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submitme': 'X'}

        response = self.get_url(self.url + '/takelogin.php', post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if re.search('donate.php', response):
            return True
        else:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_params, age=0, ep_obj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self.login():
            return results

        for mode in search_params.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                searchURL = self.urlsearch % (urllib.quote(search_string), self.categories)
                logger.log(u"Search URL: %s" % searchURL, logger.DEBUG)
                data = self.get_url(searchURL)

                if not data:
                    continue

                with BS4Parser(data, 'html5lib') as html:
                    resultsTable = html.find("table", {"class": "table2 table-bordered2"})
                    if not resultsTable:
                        continue

                    rows = resultsTable.findAll("tr")
                    for row in rows:
                        link = row.find("a", href=re.compile("details.php"))
                        if not link:
                            continue

                        title = link.text
                        download_item = row.find("a", href=re.compile("download.php"))
                        if not download_item:
                            continue

                        download_url = self.url + '/' + download_item['href']

                        # FIXME
                        size = -1
                        seeders = 1
                        leechers = 0

                        if not all([title, download_url]):
                            continue

                        # Filter unseeded torrent
                        # if seeders < self.minseed or leechers < self.minleech:
                        #    if mode != 'RSS':
                        #        logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                        #    continue

                        item = title, download_url, size, seeders, leechers
                        if mode != 'RSS':
                            logger.log(u"Found result: %s " % title, logger.DEBUG)

                        items[mode].append(item)

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seed_ratio(self):
        return self.ratio

provider = XthorProvider()
