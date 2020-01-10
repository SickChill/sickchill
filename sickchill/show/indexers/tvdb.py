# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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
import re

# Third Party Imports
import tvdbsimple
from requests.exceptions import HTTPError

# First Party Imports
# from sickbeard import logger
from sickbeard.tv import TVEpisode

# Local Folder Imports
from .base import Indexer


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = 'theTVDB'
        self.slug = 'tvdb'
        self.api_key = 'F9C450E78D99172E'
        self.show_url = 'http://thetvdb.com/?tab=series&id='
        self.base_url = 'http://thetvdb.com/api/%(apikey)s/series/'
        self.icon = 'images/indexers/thetvdb16.png'
        tvdbsimple.KEYS.API_KEY = self.api_key
        self._search = tvdbsimple.search.Search().series
        self.series = tvdbsimple.Series
        self.series_episodes = tvdbsimple.Series_Episodes
        self.series_images = tvdbsimple.Series_Images
        self.updates = tvdbsimple.Updates

    def get_series_by_id(self, indexerid, language=None):
        result = self.series(indexerid, language)
        result.info(language=language)
        return result

    def series_from_show(self, show):
        result = self.series(show.indexerid, show.lang)
        result.info(language=show.lang)
        return result

    def series_from_episode(self, episode):
        return self.series_from_show(episode.show)

    def get_series_by_name(self, name, indexerid=None, language=None):
        if indexerid:
            return self.get_series_by_id(indexerid, language)

        # Just return the first result for now
        result = self.series(self.search(name, language)[0]['id'])
        result.info(language=language)
        return result

    def episodes(self, show, season=None):
        try:
            if show.dvdorder:
                result = self.series_episodes(show.indexerid, dvdSeason=season, language=show.lang).all()
            else:
                result = self.series_episodes(show.indexerid, airedSeason=season, language=show.lang).all()
        except HTTPError:
            result = []

        return result

    def episode(self, item, season=None, episode=None, **kwargs):
        if isinstance(item, TVEpisode):
            show = item.show
            season = item.season
            episode = item.episode
        else:
            show = item

        try:
            if show.dvdorder:
                result = self.series_episodes(show.indexerid, dvdSeason=season, dvdEpisode=episode, language=show.lang, **kwargs).all()[0]
            else:
                result = self.series_episodes(show.indexerid, airedSeason=season, airedEpisode=episode, language=show.lang, **kwargs).all()[0]
        except (HTTPError, IndexError):
            result = None

        return result

    def search(self, name, language=None):
        # Caution, mistake here will cause infinite recursion
        result = []
        if re.match(r'^t?t?\d{7,8}$', name):
            result = self._search(imdbId='tt{}'.format(name.strip('t')))
        elif re.match(r'^\d{6}$', name):
            result = [self.series(name)]
        else:
            try:
                result = self._search(name, language=language)
            except HTTPError:
                if re.match(r'^(.*)[. -_]\(\d{4}\)$', name):
                    try:
                        result = self._search(name[0:-7], language=language)
                    except HTTPError:
                        if re.match(r'[. -_]', name):
                            # Recursion starts here conditionally, should be called only once
                            result = self.search(re.sub('[. -]', ' ', name), language)

        return result

    @property
    def languages(self):
        return [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]

    @property
    def lang_dict(self):
        return {
            'el': 20, 'en': 7, 'zh': 27,
            'it': 15, 'cs': 28, 'es': 16, 'ru': 22, 'nl': 13, 'pt': 26, 'no': 9,
            'tr': 21, 'pl': 18, 'fr': 17, 'hr': 31, 'de': 14, 'da': 10, 'fi': 11,
            'hu': 19, 'ja': 25, 'he': 24, 'ko': 32, 'sv': 8, 'sl': 30
        }

    @staticmethod
    def complete_image_url(location):
        location = location.strip()
        if not location:
            return location
        return 'https://artworks.thetvdb.com/banners/{path}'.format(path=location.strip())

    def __call_images_api(self, show, thumb, keyType, subKey=None):
        try:
            images = self.series_images(show.indexerid, show.lang, keyType=keyType, subKey=subKey)
            result = self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])
        except HTTPError:
            # logger.log('Unable to find image for {show}, {thumb}, {keyType}, {subKey}'.format(show=show, thumb=thumb, keyType=keyType, subKey=subKey))
            result = ''

        return result

    @staticmethod
    def actors(series):
        if hasattr(series, 'actors') and callable(series.actors):
            try:
                series.actors(series.language)
            except HTTPError:
                return []
        return series.actors

    def series_poster_url(self, show, thumb=False):
        return self.__call_images_api(show, thumb, 'poster')

    def series_banner_url(self, show, thumb=False):
        return self.__call_images_api(show, thumb, 'series')

    def series_fanart_url(self, show, thumb=False):
        return self.__call_images_api(show, thumb, 'fanart')

    def season_poster_url(self, show, season, thumb=False):
        return self.__call_images_api(show, thumb, 'season', season)

    def season_banner_url(self, show, season, thumb=False):
        return self.__call_images_api(show, thumb, 'seasonwide', season)

    def episode_image_url(self, episode):
        try:
            result = self.complete_image_url(self.episode(episode)['filename'])
        except HTTPError:
            result = ''

        return result
