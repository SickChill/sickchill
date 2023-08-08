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
    def update_library(episode_object):
        # Values from config

        if not (settings.USE_PYTIVO and settings.PYTIVO_HOST):
            return False

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
        if isinstance(episode_object, tv.TVEpisode):
            show_path = episode_object.show.location
            show_name = episode_object.show.name
            show_and_season_path = os.path.dirname(episode_object.location)
            absolute_file_path = episode_object.location
        else:
            # This is a TVShow
            show_path = episode_object.location
            show_name = episode_object.name
            show_and_season_path = os.path.dirname(episode_object.location)
            absolute_file_path = episode_object.location

        # Some show names have colons in them which are illegal in a path location, so strip them out.
        # (Are there other characters?)
        show_name = show_name.replace(":", "")

        root = show_path.replace(show_name, "")
        show_and_season_path = show_and_season_path.replace(root, "")

        container = settings.PYTIVO_SHARE_NAME + "/" + show_and_season_path
        filename = "/" + absolute_file_path.replace(root, "")

        # Finally create the url and make request
        requestUrl = (
            "http://"
            + settings.PYTIVO_HOST
            + "/TiVoConnect?"
            + urlencode({"Command": "Push", "Container": container, "File": filename, "tsn": settings.PYTIVO_TIVO_NAME})
        )

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
