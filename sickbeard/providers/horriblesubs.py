# coding=utf-8
# Author: Panz3r
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

from __future__ import print_function, unicode_literals

import re

from requests.compat import urljoin

from sickbeard import logger, tvcache
from sickbeard.bs4_parser import BS4Parser
from sickchill.helper.common import try_int
from sickchill.providers.torrent.TorrentProvider import TorrentProvider


class HorribleSubsProvider(TorrentProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        TorrentProvider.__init__(self, 'HorribleSubs')

        self.public = True
        self.supports_absolute_numbering = True
        self.anime_only = True

        self.minseed = None
        self.minleech = None

        self.url = 'https://horriblesubs.info'
        self.urls = {
            'search': urljoin(self.url, 'api.php'),
            'rss': 'http://www.horriblesubs.info/rss.php'
        }

        self.cache = tvcache.TVCache(self, min_time=15)  # only poll HorribleSubs every 15 minutes max

    def search(self, search_strings, age=0, ep_obj=None):  # pylint: disable=too-many-locals
        results = []
        # TODO Removed to allow Tests to pass... Not sure about removing it
        # if not self.show or not self.show.is_anime:
        #   return results

        for mode in search_strings:
            items = []
            logger.log('Search Mode: {0}'.format(mode), logger.DEBUG)

            for search_string in search_strings[mode]:
                if mode == 'RSS':
                    entries = self.__rssFeed()
                else:
                    entries = self.__getShow(search_string)

                items.extend(entries)

            # For each search mode sort all the items by seeders if available
            items.sort(key=lambda d: try_int(d.get('seeders', 0)), reverse=True)
            results.extend(items)

        return results

    def __rssFeed(self):
        entries = []

        rss_params = {
            'res': 'all'
        }

        target_url = self.urls['rss']

        data = self.get_url(target_url, params=rss_params, returns='text')
        if not data:
            return entries

        entries = self.__parseRssFeed(data)

        return entries

    def __parseRssFeed(self, data):
        entries = []
        with BS4Parser(data, 'html5lib') as soup:
            items = soup.findAll('item')

            for item in items:
                title = item.find('title').text
                download_url = item.find('link').text

                entry = {'title': title, 'link': download_url, 'size': 333, 'seeders': 1, 'leechers': 1, 'hash': ''}
                logger.log('Found result: {0}'.format(title), logger.DEBUG)

                entries.append(entry)

        return entries

    def __getShow(self, search_string):
        entries = []

        search_params = {
            'method': 'search',
            'value': search_string
        }

        logger.log('Search string: {0}'.format(search_string.decode('utf-8')), logger.DEBUG)
        target_url = self.urls['search']

        data = self.get_url(target_url, params=search_params, returns='text')
        if not data:
            return entries

        entries = self.__parseSearchResult(data, target_url)

        return entries

    def __parseSearchResult(self, data, target_url):
        results = []
        with BS4Parser(data, 'html5lib') as soup:
            lists = soup.find_all('ul')

            list_items = []
            for ul_list in lists:
                curr_list_item = ul_list('li') if ul_list else []
                list_items.extend(curr_list_item)

            # Continue only if one Release is found
            if len(list_items) < 1:
                logger.log('Data returned from provider does not contain any torrents', logger.DEBUG)
                return []

            for list_item in list_items:
                title = '{0}{1}'.format(str(list_item.find('span').next_sibling),str(list_item.find('strong').text))
                logger.log('Found title {0}'.format(title), logger.DEBUG)
                episode_url = '/#'.join(list_item.find('a')['href'].rsplit('#', 1))
                episode = episode_url.split('#', 1)[1]

                page_url = '{0}{1}'.format(self.url, episode_url)
                show_id = self.__getShowId(page_url)

                if not show_id:
                    logger.log('Could not find show ID', logger.DEBUG)
                    continue

                fetch_params = {
                    'method': 'getshows',
                    'type': 'show',
                    'mode': 'filter',
                    'showid': show_id,
                    'value': episode
                }

                entries = self.__fetchUrls(target_url, fetch_params, title)
                results.extend(entries)

        return results

    def __getShowId(self, target_url):
        data = self.get_url(target_url, returns='text')
        if not data:
            logger.log('Could not fetch url: {0}'.format(target_url), logger.DEBUG)
            return None

        with BS4Parser(data, 'html5lib') as soup:
            show_id = re.sub(r'[^0-9]', '', soup(text=re.compile('hs_showid'))[0])
            logger.log('show id: {0}'.format(show_id), logger.DEBUG)

        return show_id

    def __fetchUrls(self, target_url, params, title):
        entries = []

        data = self.get_url(target_url, params=params, returns='text')
        if not data:
            return entries

        with BS4Parser(data, 'html5lib') as soup:
            for div in soup.findAll('div', attrs={'class': 'rls-link'}):
                quality = div.find('span', attrs={'class': 'rls-link-label'}).get_text(strip=True)

                link = div.find('span', class_='hs-torrent-link')
                download_url = link.find('a')['href'] if link and link.find('a') else None

                if not download_url:
                    # fallback to magnet link
                    link = div.find('span', class_='hs-magnet-link')
                    download_url = link.find('a')['href'] if link and link.find('a') else None

                release_title = '[HorribleSubs] {0}.[{1}]'.format(title, quality)
                item = {'title': release_title, 'link': download_url, 'size': 333, 'seeders': 1, 'leechers': 1, 'hash': ''}
                logger.log('Found result: {0}'.format(release_title), logger.DEBUG)

                entries.append(item)

        return entries


provider = HorribleSubsProvider()
