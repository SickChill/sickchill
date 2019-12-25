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

from __future__ import print_function, unicode_literals

import tvdbsimple
from requests.exceptions import HTTPError

from sickbeard.tv import TVEpisode

from .base import Indexer


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = 'theTVDB'
        self.trakt_id = 'tvdb'
        self.api_key = 'F9C450E78D99172E'
        self.show_url = 'http://thetvdb.com/?tab=series&id='
        self.base_url = 'http://thetvdb.com/api/%(apikey)s/series/'
        self.icon = 'images/indexers/thetvdb16.png'
        tvdbsimple.KEYS.API_KEY = self.api_key
        self.search = tvdbsimple.search.Search().series
        self.series = tvdbsimple.Series
        self.series_episodes = tvdbsimple.Series_Episodes
        self.series_images = tvdbsimple.Series_Images
        self.updates = tvdbsimple.Updates

    def get_show_by_id(self, indexerid, language=None):
        result = self.series(indexerid, language)
        result.info(language=language)
        return result

    def get_show_by_name(self, name, indexerid=None, language=None):
        if indexerid:
            return self.get_show_by_id(indexerid, language)
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

    def episode(self, item, season=None, episode=None):
        if isinstance(item, TVEpisode):
            show = item.show
            season = item.season
            episode = item.episode
        else:
            show = item

        try:
            if show.dvdorder:
                result = self.series_episodes(show.indexerid, dvdSeason=season, dvdEpisode=episode, language=show.lang).all()[0]
            else:
                result = self.series_episodes(show.indexerid, airedSeason=season, airedEpisode=episode, language=show.lang).all()[0]
        except HTTPError:
            result = None

        return result

    def search(self, name, language=None):
        return self.search(name, language)

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
        return 'https://artworks.thetvdb.com/banners/{path}'.format(path=location)

    def series_poster_url(self, show, thumb=False):
        images = self.series_images(show.indexerid, show.lang, keyType='poster')
        return self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])

    def series_banner_url(self, show, thumb=False):
        images = self.series_images(show.indexerid, show.lang, keyType='series')
        return self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])

    def series_fanart_url(self, show, thumb=False):
        images = self.series_images(show.indexerid, show.lang, keyType='fanart')
        return self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])

    def season_poster_url(self, show, season, thumb=False):
        images = self.series_images(show.indexerid, show.lang, keyType='season', subKey=season)
        return self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])

    def season_banner_url(self, show, season, thumb=False):
        images = self.series_images(show.indexerid, show.lang, keyType='seasonwide', subKey=season)
        return self.complete_image_url(images.all()[0][('fileName', 'thumbnail')[thumb]])

    def episode_image_url(self, episode, thumb=False):
        return self._complete_image_url(self.episode(episode)[('fileName', 'thumbnail')[thumb]])



