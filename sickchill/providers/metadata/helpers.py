# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
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
# Third Party Imports
from requests.exceptions import HTTPError

# First Party Imports
import sickbeard
from sickbeard import helpers, logger
from sickchill import settings

meta_session = helpers.make_session()


def getShowImage(url, imgNum=None):
    if not url:
        return None

    # if they provided a fanart number try to use it instead
    if imgNum is not None:
        tempURL = url.split('-')[0] + "-" + str(imgNum) + ".jpg"
    else:
        tempURL = url

    logger.debug("Fetching image from " + tempURL)

    try:
        image_data = helpers.getURL(tempURL, session=meta_session, returns='content', allow_proxy=settings.PROXY_INDEXERS)
    except HTTPError:
        image_data = None

    if image_data is None:
        logger.warning("There was an error trying to retrieve the image, aborting")
        return

    return image_data
