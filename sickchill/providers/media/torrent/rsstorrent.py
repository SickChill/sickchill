# coding=utf-8
# # Author: Mr_Orange
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
# Stdlib Imports
import os
import re

# Third Party Imports
import bencodepy
from requests.utils import add_dict_to_cookiejar

# First Party Imports
import sickbeard
from sickbeard import helpers, logger, tvcache
from .TorrentProvider import TorrentProvider


class TorrentRssProvider(TorrentProvider):

    def __init__(self, name):

        TorrentProvider.__init__(self, name, extra_options=('daily', 'url', 'title_tag', 'cookies'))
        self.min_cache_time = 15
        self.cache = TorrentRssCache(self)

    def image_name(self):
        if os.path.isfile(os.path.join(sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME, 'images', 'providers', self.get_id() + '.png')):
            return self.get_id() + '.png'
        return 'torrentrss.png'

    def _get_title_and_url(self, item):

        title = item.get(self.config('title_tag'), '').replace(' ', '.')

        attempt_list = [
            lambda: item.get('torrent_magneturi'),
            lambda: item.enclosures[0].href,
            lambda: item.get('link')
        ]

        url = None
        for cur_attempt in attempt_list:
            try:
                url = cur_attempt()
            except Exception:
                continue

            if title and url:
                break

        return title, url

    def validateRSS(self):

        try:
            self.add_cookies_from_ui()

            # Access to a protected member of a client class
            data = self.cache.get_rss_data()['entries']
            if not data:
                return False, 'No items found in the RSS feed {0}'.format(self.url)

            title, url = self._get_title_and_url(data[0])

            if not title:
                return False, 'Unable to get title from first item'

            if not url:
                return False, 'Unable to get torrent url from first item'

            if url.startswith('magnet:') and re.search(r'urn:btih:([\w]{32,40})', url):
                return True, 'RSS feed Parsed correctly'
            else:
                torrent_file = self.get_url(url, returns='content')
                try:
                    bencodepy.decode(torrent_file)
                except (bencodepy.DecodingError, Exception) as error:
                    self.dumpHTML(torrent_file)
                    return False, 'Torrent link is not a valid torrent file: {0}'.format(error)

            return True, 'RSS feed Parsed correctly'

        except Exception as error:
            return False, 'Error when trying to load RSS: {0}'.format(str(error))

    @staticmethod
    def dumpHTML(data):
        dumpName = os.path.join(sickbeard.CACHE_DIR, 'custom_torrent.html')

        try:
            fileOut = open(dumpName, 'wb')
            fileOut.write(data)
            fileOut.close()
            helpers.chmodAsParent(dumpName)
        except IOError as error:
            logger.exception('Unable to save the file: {0}'.format(str(error)))
            return False

        logger.info('Saved custom_torrent html dump {0} '.format(dumpName))
        return True


class TorrentRssCache(tvcache.TVCache):
    def get_rss_data(self):
        if self.provider.config('cookies'):
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit('=', 1) for x in self.provider.config('cookies').split(';')))

        return self.get_rss_feed(self.provider.config('url'))
