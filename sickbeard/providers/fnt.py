# -*- coding: latin-1 -*-
# Author: raver2046 <raver2046@gmail.com> from djoole <bobby.djoole@gmail.com>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

import traceback
import re
import requests

from sickbeard import logger
from sickbeard import tvcache
from sickbeard.providers import generic
from sickbeard.bs4_parser import BS4Parser


class FNTProvider(generic.TorrentProvider):
    def __init__(self):
        generic.TorrentProvider.__init__(self, "FNT")

        self.supportsBacklog = True

        self.username = None
        self.password = None
        self.ratio = None
        self.minseed = None
        self.minleech = None

        self.cache = FNTCache(self)

        self.urls = {'base_url': 'https://fnt.nu',
                     'search': 'https://www.fnt.nu/torrents/recherche/',
                     'login': 'https://fnt.nu/account-login.php',
                    }

        self.url = self.urls['base_url']
        self.search_params = {
            "afficher": 1, "c118": 1, "c129": 1, "c119": 1, "c120": 1, "c121": 1, "c126": 1,
            "c137": 1, "c138": 1, "c146": 1, "c122": 1, "c110": 1, "c109": 1, "c135": 1, "c148": 1,
            "c153": 1, "c149": 1, "c150": 1, "c154": 1, "c155": 1, "c156": 1, "c114": 1,
            "visible": 1, "freeleech": 0, "nuke": 1, "3D": 0, "sort": "size", "order": "desc"
            }

    def _doLogin(self):

        if any(requests.utils.dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submit' : 'Se loguer'
                       }

        response = self.getURL(self.urls['login'], post_data=login_params, timeout=30)
        if not response:
            logger.log(u"Unable to connect to provider", logger.WARNING)
            return False

        if not re.search('Pseudo ou mot de passe non valide', response):
            return True
        else:
            logger.log(u"Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def _doSearch(self, search_strings, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_strings.keys():
            logger.log(u"Search Mode: %s" % mode, logger.DEBUG)
            for search_string in search_strings[mode]:

                if mode is not 'RSS':
                    logger.log(u"Search string: %s " % search_string, logger.DEBUG)

                self.search_params['recherche'] = search_string

                data = self.getURL(self.urls['search'], params=self.search_params)
                if not data:
                    continue

                try:
                    with BS4Parser(data, features=["html5lib", "permissive"]) as html:
                        result_table = html.find('table', {'id': 'tablealign3bis'})

                        if not result_table:
                            logger.log(u"Data returned from provider does not contain any torrents", logger.DEBUG)
                            continue

                        if result_table:
                            rows = result_table.findAll("tr", {"class" : "ligntorrent"})

                            for row in rows:
                                link = row.findAll('td')[1].find("a", href=re.compile("fiche_film"))

                                if link:
                                    try:
                                        title = link.text
                                        download_url = self.urls['base_url'] + "/" + row.find("a", href=re.compile(r"download\.php"))['href']
                                    except (AttributeError, TypeError):
                                        continue

                                    try:
                                        detailseedleech = link['mtcontent']
                                        seeders = int(detailseedleech.split("<font color='#00b72e'>")[1].split("</font>")[0])
                                        leechers = int(detailseedleech.split("<font color='red'>")[1].split("</font>")[0])
                                        # FIXME
                                        size = -1
                                    except Exception:
                                        logger.log(u"Unable to parse torrent id & seeders & leechers. Traceback: %s " % traceback.format_exc(), logger.DEBUG)
                                        continue

                                    if not all([title, download_url]):
                                        continue

                                    # Filter unseeded torrent
                                    if seeders < self.minseed or leechers < self.minleech:
                                        if mode is not 'RSS':
                                            logger.log(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers), logger.DEBUG)
                                        continue

                                    item = title, download_url, size, seeders, leechers
                                    if mode is not 'RSS':
                                        logger.log(u"Found result: %s " % title, logger.DEBUG)

                                    items[mode].append(item)

                except Exception, e:
                    logger.log(u"Failed parsing provider. Traceback: %s" % traceback.format_exc(), logger.ERROR)

            # For each search mode sort all the items by seeders if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio


class FNTCache(tvcache.TVCache):
    def __init__(self, provider_obj):
        tvcache.TVCache.__init__(self, provider_obj)

        # Only poll FNT every 10 minutes max
        self.minTime = 10

    def _getRSSData(self):
        search_strings = {'RSS': ['']}
        return {'entries': self.provider._doSearch(search_strings)}


provider = FNTProvider()
