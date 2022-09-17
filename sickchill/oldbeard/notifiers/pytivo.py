import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import requests

from sickchill import logger, settings, tv


class Notifier(object):
    def notify_snatch(self, ep_name):
        pass

    def notify_download(self, ep_name):
        pass

    def notify_subtitle_download(self, ep_name, lang):
        pass

    def notify_update(self, new_version):
        pass

    def notify_login(self, ipaddress=""):
        pass

    @staticmethod
    def update_library(ep_obj):

        # Values from config

        if not settings.USE_PYTIVO:
            return False

        host = settings.PYTIVO_HOST
        shareName = settings.PYTIVO_SHARE_NAME
        tsn = settings.PYTIVO_TIVO_NAME

        # There are two more values required, the container and file.
        #
        # container: The share name, show name and season
        #
        # file: The file name
        #
        # Some slicing and dicing of variables is required to get at these values.
        #
        # There might be better ways to arrive at the values, but this is the best I have been able to
        # come up with.
        #

        # Calculated values
        # noinspection PyUnresolvedReferences
        if isinstance(ep_obj, tv.TVEpisode):
            showPath = ep_obj.show.location
            showName = ep_obj.show.name
            rootShowAndSeason = os.path.dirname(ep_obj.location)
            absPath = ep_obj.location
        else:
            # This is a TVShow
            showPath = ep_obj.location
            showName = ep_obj.name
            rootShowAndSeason = os.path.dirname(ep_obj.location)
            absPath = ep_obj.location

        # Some show names have colons in them which are illegal in a path location, so strip them out.
        # (Are there other characters?)
        showName = showName.replace(":", "")

        root = showPath.replace(showName, "")
        showAndSeason = rootShowAndSeason.replace(root, "")

        container = shareName + "/" + showAndSeason
        filename = "/" + absPath.replace(root, "")

        # Finally create the url and make request
        requestUrl = "http://" + host + "/TiVoConnect?" + urlencode({"Command": "Push", "Container": container, "File": filename, "tsn": tsn})

        logger.debug("pyTivo notification: Requesting " + requestUrl)

        request = Request(requestUrl)

        try:
            urlopen(request)
        except requests.exceptions.RequestException as error:
            if hasattr(error, "reason"):
                logger.exception(f"pyTivo notification: Error, failed to reach a server - {error.reason}")
                return False
            elif hasattr(error, "code"):
                logger.exception(f"pyTivo notification: Error, the server couldn't fulfill the request - {error.code}")
            return False
        except Exception as error:
            logger.exception(f"PYTIVO: Unknown exception: {error}")
            return False
        else:
            logger.info("pyTivo notification: Successfully requested transfer of file")
            return True
