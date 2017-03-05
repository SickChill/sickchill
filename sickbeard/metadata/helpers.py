# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
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

from __future__ import print_function, unicode_literals

from sickbeard import helpers
from sickbeard import logger

meta_session = helpers.make_session()


def getShowImage(url, imgNum=None):
    if url is None:
        return None

    # if they provided a fanart number try to use it instead
    if imgNum is not None:
        tempURL = url.split('-')[0] + "-" + str(imgNum) + ".jpg"
    else:
        tempURL = url

    logger.log("Fetching image from " + tempURL, logger.DEBUG)

    image_data = helpers.getURL(tempURL, session=meta_session, returns='content')
    if image_data is None:
        logger.log("There was an error trying to retrieve the image, aborting", logger.WARNING)
        return

    return image_data
