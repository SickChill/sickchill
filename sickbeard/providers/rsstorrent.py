# coding=utf-8
# # Author: Mr_Orange
#
# URL: https://sickrage.github.io
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

import io
import os
import re
from requests.utils import add_dict_to_cookiejar
from bencode import bdecode

import sickbeard
from sickbeard import helpers, logger, tvcache

from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex
from sickrage.providers.torrent.TorrentProvider import TorrentProvider


class TorrentRssProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self, name, url, cookies='',  # pylint: disable=too-many-arguments
                 titleTAG='title', search_mode='eponly', search_fallback=False,
                 enable_daily=False, enable_backlog=False):

        TorrentProvider.__init__(self, name)

        self.cache = TorrentRssCache(self, min_time=15)
        self.url = url.rstrip('/')

        self.ratio = None
        self.supports_backlog = False

        self.search_mode = search_mode
        self.search_fallback = search_fallback
        self.enable_daily = enable_daily
        self.enable_backlog = enable_backlog
        self.cookies = cookies
        self.titleTAG = titleTAG

    def configStr(self):  # pylint: disable=too-many-arguments
        return "%s|%s|%s|%s|%d|%s|%d|%d|%d" % (
            self.name or '',
            self.url or '',
            self.cookies or '',
            self.titleTAG or '',
            self.enabled,
            self.search_mode or '',
            self.search_fallback,
            self.enable_daily,
            self.enable_backlog
        )

    @staticmethod
    def get_providers_list(data):
        providers_list = [x for x in [TorrentRssProvider._make_provider(x) for x in data.split('!!!')] if x]
        seen_values = set()
        providers_set = []

        for provider in providers_list:
            value = provider.name

            if value not in seen_values:
                providers_set.append(provider)
                seen_values.add(value)

        return [x for x in providers_set if x]

    def image_name(self):
        if ek(os.path.isfile, ek(os.path.join, sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME, 'images', 'providers', self.get_id() + '.png')):
            return self.get_id() + '.png'
        return 'torrentrss.png'

    def _get_title_and_url(self, item):

        title = item.get(self.titleTAG, '').replace(' ', '.')

        attempt_list = [lambda: item.get('torrent_magneturi'),

                        lambda: item.enclosures[0].href,

                        lambda: item.get('link')]

        url = None
        for cur_attempt in attempt_list:
            try:
                url = cur_attempt()
            except Exception:
                continue

            if title and url:
                break

        return title, url

    @staticmethod
    def _make_provider(config):
        if not config:
            return None

        cookies = None
        enable_backlog = 0
        enable_daily = 0
        search_fallback = 0
        search_mode = 'eponly'
        title_tag = 'title'

        try:
            values = config.split('|')

            if len(values) == 9:
                name, url, cookies, title_tag, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            elif len(values) == 8:
                name, url, cookies, enabled, search_mode, search_fallback, enable_daily, enable_backlog = values
            else:
                enabled = values[4]
                name = values[0]
                url = values[1]
        except ValueError:
            logger.log(u'Skipping RSS Torrent provider string: \'%s\', incorrect format' % config, logger.ERROR)
            return None

        new_provider = TorrentRssProvider(
            name, url, cookies=cookies, titleTAG=title_tag, search_mode=search_mode,
            search_fallback=search_fallback, enable_daily=enable_daily, enable_backlog=enable_backlog
        )
        new_provider.enabled = enabled == '1'

        return new_provider

    def validateRSS(self):  # pylint: disable=too-many-return-statements

        try:
            if self.cookies:
                cookie_validator = re.compile(r"^(\w+=\w+)(;\w+=\w+)*$")
                if not cookie_validator.match(self.cookies):
                    return False, 'Cookie is not correctly formatted: ' + self.cookies

            # pylint: disable=protected-access
            # Access to a protected member of a client class
            data = self.cache._getRSSData()['entries']
            if not data:
                return False, 'No items found in the RSS feed ' + self.url

            (title, url) = self._get_title_and_url(data[0])

            if not title:
                return False, 'Unable to get title from first item'

            if not url:
                return False, 'Unable to get torrent url from first item'

            if url.startswith('magnet:') and re.search(r'urn:btih:([\w]{32,40})', url):
                return True, 'RSS feed Parsed correctly'
            else:
                if self.cookies:
                    add_dict_to_cookiejar(self.session.cookies, dict(x.rsplit('=', 1) for x in self.cookies.split(';')))
                torrent_file = self.get_url(url, need_bytes=True)
                try:
                    bdecode(torrent_file)
                except Exception as e:
                    self.dumpHTML(torrent_file)
                    return False, 'Torrent link is not a valid torrent file: {}'.format(ex(e))

            return True, 'RSS feed Parsed correctly'

        except Exception as e:
            return False, 'Error when trying to load RSS: ' + ex(e)

    @staticmethod
    def dumpHTML(data):
        dumpName = ek(os.path.join, sickbeard.CACHE_DIR, 'custom_torrent.html')

        try:
            fileOut = io.open(dumpName, 'wb')
            fileOut.write(data)
            fileOut.close()
            helpers.chmodAsParent(dumpName)
        except IOError as e:
            logger.log(u"Unable to save the file: %s " % repr(e), logger.ERROR)
            return False
        logger.log(u"Saved custom_torrent html dump %s " % dumpName, logger.INFO)
        return True

    def seed_ratio(self):
        return self.ratio


class TorrentRssCache(tvcache.TVCache):
    def _getRSSData(self):
        logger.log(u"Cache update URL: %s" % self.provider.url, logger.DEBUG)

        if self.provider.cookies:
            add_dict_to_cookiejar(self.provider.session.cookies, dict(x.rsplit('=', 1) for x in self.provider.cookies.split(';')))

        return self.getRSSFeed(self.provider.url)
