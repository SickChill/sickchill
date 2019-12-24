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

from requests.exceptions import HTTPError

import tvdbsimple

from .base import Indexer
from sickbeard.tv import TVEpisode


class TVDB(Indexer):
    def __init__(self):
        super(TVDB, self).__init__()
        self.name = 'theTVDB'
        self.trakt_id = 'tvdb'
        self.api_key = 'F9C450E78D99172E'
        tvdbsimple.KEYS.API_KEY = self.api_key
        self.search = tvdbsimple.search.Search().series
        self.series = tvdbsimple.series.Series
        self.series_episodes = tvdbsimple.series.Series_Episodes
        self.series_images = tvdbsimple.series.Series_Images

    def get_show_by_id(self, indexerid, language=None):
        result = self.series(indexerid, language)
        result.info()
        return result

    def get_show_by_name(self, name, indexerid=None, language=None):
        if indexerid:
            return self.get_show_by_id(indexerid, language)
        # Just return the first result for now
        return self.series(self.search(name, language)[0]['id'])

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

    def series_title(self, show):
        series = self.get_show_by_id(show.indexerid, language=show.lang)
        series.info(language=show.lang)
        return series.seriesName

    @property
    def languages(self):
        return [
            "da", "fi", "nl", "de", "it", "es", "fr", "pl", "hu", "el", "tr",
            "ru", "he", "ja", "pt", "zh", "cs", "sl", "hr", "ko", "en", "sv", "no"
        ]

    @staticmethod
    def _complete_image_url(location):
        return 'https://artworks.thetvdb.com/banners/{path}'.format(path=location)

    def episode_image_url(self, episode):
        return self._complete_image_url(self.episode(episode)['filename'])
