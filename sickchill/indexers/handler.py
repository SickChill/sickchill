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

# import re

import sickbeard
from sickbeard import logger
from sickbeard.tv import Show

from .tvdb import TVDB

INDEXER_TVDB = 1
INDEXER_TVRAGE = 2  # Must keep


class ShowIndexer(object):

    def __init__(self):
        self.indexers = {INDEXER_TVDB: TVDB()}
        if sickbeard.INDEXER_DEFAULT is None:
            sickbeard.INDEXER_DEFAULT = INDEXER_TVDB

    def __getitem__(self, item):
        return self.indexers[item]

    def name(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].name

    def trakt_id(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].trakt_id

    def search(self, indexer=None, *args, **kwargs):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].search(*args, **kwargs)

    def search_indexers_for_show_name(self, name, indexerid=None, language=None):
        results = {}
        for i, indexer in self.indexers.iteritems():
            results[i] = indexer.search(name, language)

        return results

    def search_indexers_for_show_id(self, name=None, indexer=None, indexerid=None):
        if not indexer:
            indexer = self.indexers.keys()

        if isinstance(indexer, (int, basestring)):
            indexer = [indexer]

        if isinstance(name, basestring):
            name = [name]

        if indexerid:
            indexerid = int(indexerid)

        for n in name:
            # n = [re.sub('[. -]', ' ', n)]
            for i in indexer:

                logger.log("Trying to find {} on {}".format(name, self.indexers[i].name), logger.DEBUG)
                if indexerid:
                    result = self.indexers[i].get_show_by_id(indexerid)
                else:
                    result = self.indexers[i].get_show_by_name(n)

                try:
                    garbage = result.seriesName, result.id
                except AttributeError:
                    logger.log("Failed to find {} on {}".format(name, self.indexers[i].name), logger.DEBUG)
                    continue

                ShowObj = Show.find(sickbeard.showList, result.id)
                if indexerid and ShowObj and ShowObj.indexerid == result.id:
                    return i, result
                elif indexerid and indexerid == result.id:
                    return i, result

        return None, None

    @property
    def languages(self, indexer=None):
        if indexer is None:
            indexer = sickbeard.INDEXER_DEFAULT
        return self.indexers[indexer].languages

    def episodes(self, show, season):
        return self.indexers[show.indexer].episodes(show, season)

    def episode(self, item, season=None, episode=None):
        if isinstance(item, sickbeard.tv.TVEpisode):
            show = item.show
            season = item.season
            episode = item.episode
        else:
            show = item

        return self.indexers[show.indexer].episode(show, season, episode)

    def episode_image_url(self, episode):
        return self.indexers[episode.show.indexer].episode_image_url(episode)


