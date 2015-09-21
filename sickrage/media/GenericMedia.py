# This file is part of SickRage.
#
# URL: https://www.sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import sickbeard

from abc import abstractmethod
from mimetypes import guess_type
from os.path import isfile, join, normpath
from sickbeard.helpers import findCertainShow
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import MultipleShowObjectsException


class GenericMedia:
    def __init__(self, indexer_id, media_format='normal'):
        """
        :param indexer_id: The indexer id of the show
        :param media_format: The format of the media to get. Must be either 'normal' or 'thumb'
        """

        if media_format in ('normal', 'thumb'):
            self.media_format = media_format
        else:
            self.media_format = 'normal'

        try:
            self.indexer_id = int(indexer_id)
        except ValueError:
            self.indexer_id = 0

    @abstractmethod
    def get_default_media_name(self):
        """
        :return: The name of the file to use as a fallback if the show media file is missing
        """

        return ''

    def get_media(self):
        """
        :return: The content of the desired media file
        """

        static_media_path = self.get_static_media_path()

        if ek(isfile, static_media_path):
            with open(static_media_path, 'rb') as content:
                return content.read()

        return None

    @abstractmethod
    def get_media_path(self):
        """
        :return: The path to the media related to ``self.indexer_id``
        """

        return ''

    @staticmethod
    def get_media_root():
        """
        :return: The root folder containing the media
        """

        return ek(join, sickbeard.PROG_DIR, 'gui', 'slick')

    def get_media_type(self):
        """
        :return: The mime type of the current media
        """

        static_media_path = self.get_static_media_path()

        if ek(isfile, static_media_path):
            return guess_type(static_media_path)[0]

        return ''

    def get_show(self):
        """
        :return: The show object associated with ``self.indexer_id`` or ``None``
        """

        try:
            return findCertainShow(sickbeard.showList, self.indexer_id)
        except MultipleShowObjectsException:
            return None

    def get_static_media_path(self):
        """
        :return: The full path to the media
        """

        if self.get_show():
            media_path = self.get_media_path()

            if ek(isfile, media_path):
                return normpath(media_path)

        image_path = ek(join, self.get_media_root(), 'images', self.get_default_media_name())

        return image_path.replace('\\', '/')
