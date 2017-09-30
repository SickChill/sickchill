# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: http://sickrage.github.io
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re

import feedparser
import validators
from requests.compat import urljoin
from sickbeard import logger, tvcache
from sickrage.helper.common import convert_size, try_int
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class SkyTorrents(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, "SkyTorrents")

        self.public = True

        self.minseed = None
        self.minleech = None

        self.url = "https://www.skytorrents.in"
        self.urls = {"search": urljoin(self.url, "/rss/all/{sorting}/{page}/{search_string}")}

        self.custom_url = None

        self.cache = tvcache.TVCache(self, search_params={"RSS": [""]})

        self.regex = re.compile('(?P<seeders>\d+) seeder\(s\), (?P<leechers>\d+) leecher\(s\), (\d+) file\(s\) (?P<size>[^\]]*)')

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []

        """
            sorting
            ss: relevance
            ed: seeds desc
            ea: seeds asc
            pd: peers desc
            pa: peers asc
            sd: big > small
            sa: small > big
            ad: added desc (latest)
            aa: added asc (oldest)
        """
        for mode in search_strings:
            items = []
            logger.log("Search Mode: {0}".format(mode), logger.DEBUG)
            for search_string in search_strings[mode]:
                if mode != "RSS":
                    logger.log("Search string: {0}".format
                               (search_string.decode("utf-8")), logger.DEBUG)

                search_url = self.urls["search"].format(sorting=("ed", "ad")[mode == "RSS"], page=1, search_string=search_string)
                if self.custom_url:
                    if not validators.url(self.custom_url):
                        logger.log("Invalid custom url: {0}".format(self.custom_url), logger.WARNING)
                        return results
                    search_url = urljoin(self.custom_url, search_url.split(self.url)[1])

                data = self.get_url(search_url, returns="text")
                if not data:
                    logger.log("URL did not return results/data, if the results are on the site maybe try a custom url, or a different one", logger.DEBUG)
                    continue

                if not data.startswith("<rss"):
                    logger.log("Expected rss but got something else, is your mirror failing?", logger.INFO)
                    continue

                feed = feedparser.parse(data)
                for item in feed.entries:
                    try:
                        title = item.title
                        download_url = item.link
                        if not (title and download_url):
                            continue

                        info = self.regex.search(item.description)
                        if not info:
                            continue

                        seeders = try_int(info.group("seeders"))
                        leechers = try_int(info.group("leechers"))
                        if seeders < self.minseed or leechers < self.minleech:
                            if mode != "RSS":
                                logger.log("Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format
                                           (title, seeders, leechers), logger.DEBUG)
                            continue

                        category = item.category
                        if category != 'all':
                            logger.log('skytorrents.in has added categories! Please report this so it can be updated: Category={cat}, '
                                       'Title={title}'.format(cat=category, title=title), logger.ERROR)

                        size = convert_size(info.group('size')) or -1
                        
                        info_hash = download_url.rsplit('/', 2)[1]

                        item = {'title': title, 'link': download_url, 'size': size, 'seeders': seeders, 'leechers': leechers, 'hash': info_hash}
                        if mode != "RSS":
                            logger.log("Found result: {0} with {1} seeders and {2} leechers".format(title, seeders, leechers), logger.DEBUG)

                        items.append(item)

                    except (AttributeError, TypeError, KeyError, ValueError):
                        continue

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)

            results += items

        return results

provider = SkyTorrents()
