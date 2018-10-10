# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sick-rage.github.io
# Git: https://github.com/SickChill/SickChill.git
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

from __future__ import unicode_literals

from datetime import datetime

from feedparser.util import FeedParserDict
from hachoir_parser import createParser

import sickbeard
from sickbeard import logger
from sickbeard.classes import Proper, TorrentSearchResult
from sickbeard.common import Quality
from sickbeard.db import DBConnection
from sickchill.helper.common import try_int
from sickchill.helper.exceptions import ex
from sickchill.providers.GenericProvider import GenericProvider
from sickchill.show.Show import Show


class TorrentProvider(GenericProvider):
    def __init__(self, name):
        GenericProvider.__init__(self, name)
        self.ratio = None
        self.provider_type = GenericProvider.TORRENT

    def find_propers(self, search_date=None):
        results = []
        db = DBConnection()
        placeholder = ','.join([str(x) for x in Quality.DOWNLOADED + Quality.SNATCHED + Quality.SNATCHED_BEST])
        sql_results = db.select(
            'SELECT s.show_name, e.showid, e.season, e.episode, e.status, e.airdate'
            ' FROM tv_episodes AS e'
            ' INNER JOIN tv_shows AS s ON (e.showid = s.indexer_id)'
            ' WHERE e.airdate >= ' + str(search_date.toordinal()) +
            ' AND e.status IN (' + placeholder + ') and e.is_proper = 0'
        )

        for result in sql_results or []:
            show = Show.find(sickbeard.showList, int(result[b'showid']))

            if show:
                episode = show.getEpisode(result[b'season'], result[b'episode'])

                for term in self.proper_strings:
                    search_strings = self._get_episode_search_strings(episode, add_string=term)

                    for search_string in search_strings:
                        for item in self.search(search_string):
                            title, url = self._get_title_and_url(item)

                            results.append(Proper(title, url, datetime.today(), show))

        return results

    @property
    def is_active(self):
        return bool(sickbeard.USE_TORRENTS) and self.is_enabled

    @property
    def _custom_trackers(self):
        if not (sickbeard.TRACKERS_LIST and self.public):
            return ''

        return '&tr=' + '&tr='.join({x.strip() for x in sickbeard.TRACKERS_LIST.split(',') if x.strip()})

    def _get_result(self, episodes):
        return TorrentSearchResult(episodes)

    def _get_size(self, item):
        if isinstance(item, dict):
            size = item.get('size', -1)
        elif isinstance(item, (list, tuple)) and len(item) > 2:
            size = item[2]
        else:
            size = -1

        # Make sure we didn't select seeds/leechers by accident
        if not size or size < 1024 * 1024:
            size = -1

        return try_int(size, -1)

    def _get_storage_dir(self):
        return sickbeard.TORRENT_DIR

    def _get_title_and_url(self, item):
        if isinstance(item, (dict, FeedParserDict)):
            download_url = item.get('url', '')
            title = item.get('title', '')

            if not download_url:
                download_url = item.get('link', '')
        elif isinstance(item, (list, tuple)) and len(item) > 1:
            download_url = item[1]
            title = item[0]
        else:
            download_url = ''
            title = ''

        if title.endswith('DIAMOND'):
            logger.log('Skipping DIAMOND release for mass fake releases.')
            download_url = title = 'FAKERELEASE'

        if download_url:
            download_url = download_url.replace('&amp;', '&')

        if title:
            title = title.replace(' ', '.')

        return title, download_url

    def _verify_download(self, file_name=None):
        try:
            parser = createParser(file_name)

            if parser:
                # pylint: disable=protected-access
                # Access to a protected member of a client class
                mime_type = parser._getMimeType()

                try:
                    parser.stream._input.close()
                except Exception:
                    pass

                if mime_type == 'application/x-bittorrent':
                    return True
        except Exception as e:
            logger.log('Failed to validate torrent file: {0}'.format(ex(e)), logger.DEBUG)

        logger.log('Result is not a valid torrent file', logger.DEBUG)
        return False

    def seed_ratio(self):
        return self.ratio
