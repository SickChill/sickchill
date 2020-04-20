# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import datetime
import time

# Third Party Imports
from requests.compat import urljoin

# First Party Imports
from sickbeard import db, logger, tvcache
from sickchill.helper.common import try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider

try:
    # https://github.com/SickChill/SickChill/issues/6236
    # Python lower than 2.7.9 Throws a syntax error here.
    import js2py
except SyntaxError:
    js2py = None




class ThePirateBayProvider(TorrentProvider):

    def __init__(self):

        # Provider Init
        TorrentProvider.__init__(self, "ThePirateBay")

        # Credentials
        self.public = True

        # Torrent Stats
        self.minseed = None
        self.minleech = None
        self.confirmed = True

        # URLs
        self.url = "https://thepiratebay.org"
        self.api = "https://apibay.org"
        self.queries = {
            'top': ['top100:208', 'top100:205']
        }
        self.script_url = "https://torrindex.net/static/main.js"

        # "https://apibay.org/precompiled/data_top100_48h_205.json"
        # "https://apibay.org/precompiled/data_top100_48h_208.json"
        #
        # "https://apibay.org/q.php?q=Arrow S08E08&cat=205,208"
        # "https://apibay.org/q.php?q=tt2193021&cats=205,208"

        self.urls = {
            "search": urljoin(self.api, "q.php"),
            "rss": [
                urljoin(self.api, "precompiled/data_top100_48h_208.json"),
                urljoin(self.api, "precompiled/data_top100_48h_205.json")
            ]
        }

        # Cache
        self.cache = tvcache.TVCache(self, min_time=30)  # only poll ThePirateBay every 30 minutes max

    @property
    def tracker_cache(self):
        return TrackerCacheDBConnection(self)

    def get_tracker_list(self):
        if js2py is None:
            return ''

        script = self.get_url(self.script_url)
        context = js2py.EvalJs()
        context.execute(
            """
            escape = function(text){pyimport urllib; return urllib.quote(text)};
            unescape = function(text){pyimport urllib; return urllib.unquote(text)};
            encodeURI = function(text){pyimport urllib; return urllib.quote(text, safe='~@#$&()*!+=:;,.?/\\'')};
            decodeURI = unescape;
            encodeURIComponent = function(text){pyimport urllib; return urllib.quote(text, safe='~()*!.\\'')};
            decodeURIComponent = unescape;
            """
        )

        context.execute(script)
        return context.print_trackers()

    def make_magnet(self, name, info_hash):
        trackers = self.tracker_cache.get_trackers()
        return "magnet:?xt=urn:btih:{info_hash}&dn={name}{trackers}".format(name=name, info_hash=info_hash, trackers=trackers) + self._custom_trackers

    def search(self, search_strings, age=0, ep_obj=None):
        results = []
        search_params = {
            "cat": '208,205',
            "q": None
        }

        if not (self.get_tracker_list() or self._custom_trackers):
            logger.log("Cannot use tpb provider without python 2.7.9+ unless you set some custom trackers in config/search on the torrents tab. Re-enable "
                       "this provider after fixing this issue.")
            self.enabled = False
            return results

        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)

            all_search_strings = search_strings[mode]
            if mode != "RSS" and self.show and self.show.imdbid:
                all_search_strings = [self.show.imdbid] + search_strings[mode]

            for search_string in all_search_strings:
                search_urls = (self.urls["search"], self.urls["rss"])[mode == "RSS"]
                if not isinstance(search_urls, list):
                    search_urls = [search_urls]

                for search_url in search_urls:
                    if mode != "RSS":
                        search_params["q"] = search_string
                        logger.log("Search string: {}".format(search_string.decode("utf-8")), logger.DEBUG)

                        data = self.get_url(search_url, params=search_params, returns="json")
                    else:
                        data = self.get_url(search_url, returns="json")

                    if not data:
                        logger.log("URL did not return data", logger.DEBUG)
                        continue

                    for result in data:
                        try:
                            title = result['name']
                            if title == "No results returned":
                                logger.log(title, logger.DEBUG)
                                continue

                            info_hash = result['info_hash']
                            if not all([title, info_hash]):
                                continue

                            seeders = result['seeders']
                            leechers = result['leechers']

                            # Filter unseeded torrent
                            if seeders < self.minseed or leechers < self.minleech:
                                if mode != "RSS":
                                    logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                               (title, seeders, leechers), logger.DEBUG)
                                continue

                            # Accept Torrent only from Good People for every Episode Search
                            if self.confirmed and not result['status'] in ('trusted', 'vip'):
                                if mode != "RSS":
                                    logger.log("Found result: {0} but that doesn't seem like a trusted result so I'm ignoring it".format(title), logger.DEBUG)
                                continue

                            torrent_size = try_int(result['size'])

                            item = {'title': title, 'link': self.make_magnet(title, info_hash), 'size': torrent_size, 'seeders': seeders, 'leechers': leechers,
                                    'hash': info_hash}
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


class TrackerCacheDBConnection(db.DBConnection):
    def __init__(self, provider_instance=None, update_frequency=datetime.timedelta(hours=8)):
        super(TrackerCacheDBConnection, self).__init__('cache.db')
        if not self.has_table('trackers'):
            self.action("CREATE TABLE trackers (provider TEXT, time NUMERIC, trackers TEXT)")

        self.provider = provider_instance
        self.provider_id = provider_instance.get_id()
        self.update_frequency = update_frequency

    def get_trackers(self):
        sql_result = self.select_one("SELECT * FROM trackers WHERE provider = ?", [self.provider_id])
        if sql_result:
            last_time = datetime.datetime.fromtimestamp(sql_result[b"time"])
            if last_time > datetime.datetime.now():
                last_time = datetime.datetime.min
        else:
            last_time = datetime.datetime.min

        if datetime.datetime.now() - last_time > self.update_frequency:
            trackers = self.provider.get_tracker_list()

            self.upsert(
                "trackers",
                {'time': int(time.mktime(datetime.datetime.now().timetuple())), 'trackers': trackers},
                {'provider': self.provider_id},
            )
            result = trackers
        else:
            result = sql_result[b'trackers']

        return result


provider = ThePirateBayProvider()
