# coding=utf-8
#
# URL: https://sick-rage.github.io
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

"""
Recommend shows based on lists from indexers
"""

from __future__ import print_function, unicode_literals

import os
import posixpath

import sickbeard
from sickbeard import helpers
from sickrage.helper.encoding import ek


class RecommendedShow(object):
    """
    Base class for show recommendations
    """
    def __init__(self, show_id, title, indexer, indexer_id, cache_subfolder='recommended',
                 rating=None, votes=None, image_href=None, image_src=None):
        """
        Create a show recommendation

        :param show_id: as provided by the list provider
        :param title: of the show as displayed in the recommended show page
        :param indexer: used to map the show to
        :param indexer_id: a mapped indexer_id for indexer
        :param cache_subfolder: to store images
        :param rating: of the show in percent
        :param votes: number of votes
        :param image_href: the href when clicked on the show image (poster)
        :param image_src: the url to the "cached" image (poster)
        """
        self.show_id = show_id
        self.title = title
        self.indexer = indexer
        self.indexer_id = indexer_id
        self.cache_subfolder = cache_subfolder
        self.rating = rating
        self.votes = votes
        self.image_href = image_href
        self.image_src = image_src

        # Check if the show is currently already in the db
        self.show_in_list = self.indexer_id in {show.indexerid for show in sickbeard.showList if show.indexerid}
        self.session = helpers.make_session()

    def cache_image(self, image_url):
        """
        Store cache of image in cache dir

        :param image_url: Source URL
        """
        if not self.cache_subfolder:
            return

        self.image_src = ek(posixpath.join, 'images', self.cache_subfolder, ek(os.path.basename, image_url))

        path = ek(os.path.abspath, ek(os.path.join, sickbeard.CACHE_DIR, 'images', self.cache_subfolder))

        if not ek(os.path.exists, path):
            ek(os.makedirs, path)

        full_path = ek(posixpath.join, path, ek(os.path.basename, image_url))

        if not ek(os.path.isfile, full_path):
            helpers.download_file(image_url, full_path, session=self.session)
