# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# Contributor: pluzun <pluzun59@gmail.com>
#
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import re

# Third Party Imports
from requests.compat import urljoin
from requests.utils import dict_from_cookiejar

# First Party Imports
from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import convert_size, try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class TorrentLeechProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "TorrentLeech")

        # Credentials
        self.username = None
        self.password = None

        # Torrent Stats
        self.minseed = None
        self.minleech = None

        # URLs
        self.url = "https://www.torrentleech.org"
        self.urls = {
            "login": urljoin(self.url, "user/account/login/"),
            "search": urljoin(self.url, "torrents/browse/list/"),
            "download": urljoin(self.url, "download/"),
        }

        # Proper Strings
        self.proper_strings = ["PROPER", "REPACK"]

        # Cache
        self.cache = tvcache.TVCache(self)

    def login(self):
        if any(dict_from_cookiejar(self.session.cookies).values()):
            return True

        login_params = {
            "username": self.username.encode("utf-8"),
            "password": self.password.encode("utf-8"),
        }

        response = self.get_url(self.urls["login"], post_data=login_params, returns="text")
        if not response:
            logger.log("Unable to connect to provider", logger.WARNING)
            return False

        if re.search("Invalid Username/password", response) or re.search("<title>Login :: TorrentLeech.org</title>", response):
            logger.log("Invalid username or password. Check your settings", logger.WARNING)
            return False

        return True

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
        results = []
        if not self.login():
            return results

        # TV, Episodes, BoxSets, Episodes HD, Animation, Anime, Cartoons
        # 2,26,27,32,7,34,35

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:

                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                    categories = ["2", "7", "35"]
                    categories += ["26", "32"] if mode == "Episode" else ["27"]
                    if self.show and self.show.is_anime:
                        categories += ["34"]
                else:
                    categories = ["2", "26", "27", "32", "7", "34", "35"]

                # Craft the query URL
                categories_url = 'categories/{categories}/'.format(categories=",".join(categories))
                query_url = 'query/{query_string}'.format(query_string=search_string)
                params_url = urljoin(categories_url, query_url)
                search_url = urljoin(self.urls['search'], params_url)

                data = self.get_url(search_url, returns='json')
                if not data:
                    logger.log("No data returned from provider", logger.DEBUG)
                    continue

                # TODO: Handle more than 35 torrents in return. (Max 35 per call)
                torrent_list = data['torrentList']

                if len(torrent_list) < 1:
                    logger.log("Data returned from provider does not contain any torrents", logger.DEBUG)
                    continue

                for torrent in torrent_list:
                    try:
                        title = torrent['name']
                        download_url = urljoin(self.urls['download'], '{id}/{filename}'.format(id=torrent['fid'], filename=torrent['filename']))

                        seeders = torrent['seeders']
                        leechers = torrent['leechers']

                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.log("Discarding torrent because it doesn't meet the"
                                            " minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                            (title, seeders, leechers), logger.DEBUG)
                                continue

                        size = torrent['size']

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': ''}

                        if mode != "RSS":
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format
                                       (title, seeders, leechers), logger.DEBUG)

                        items.append(item)
                    except StandardError:
                        continue


            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results += items

        return results


provider = TorrentLeechProvider()
