# coding=utf-8
# This file is part of SickChill.
#
# URL: https://sickchill.github.io
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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# First Party Imports
from sickbeard.image_cache import ImageCache
from sickchill.media.GenericMedia import GenericMedia


class ShowPoster(GenericMedia):
    """
    Get the poster of a show
    """

    def get_default_media_name(self):
        return 'poster.png'

    def get_media_path(self):
        if self.get_show():
            if self.media_format == 'normal':
                return ImageCache().poster_path(self.indexer_id)

            if self.media_format == 'thumb':
                return ImageCache().poster_thumb_path(self.indexer_id)

        return ''
