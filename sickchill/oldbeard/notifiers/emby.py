from urllib.parse import urljoin

import requests

from sickchill import logger, settings


class Notifier(object):
    def __init__(self):
        self.session = None

    def __make_session(self, emby_apikey=None):
        if not self.session:
            self.session = requests.Session()

        self.session.headers.update({"X-Emby-Token": emby_apikey or settings.EMBY_APIKEY, "Content-Type": "application/json"})
        return self.session

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """
        url = urljoin(host or settings.EMBY_HOST, "emby/Notifications/Admin")
        params = {"Name": "SickChill", "Description": message, "ImageUrl": settings.LOGO_URL}

        try:
            session = self.__make_session(emby_apikey)
            response = session.get(url, params=params)
            if response:
                logger.debug("EMBY: HTTP response: {0}".format(response.text.replace("\n", "")))
            response.raise_for_status()

            return True
        except requests.exceptions.RequestException as error:
            logger.warning(f"EMBY: Warning: Could not contact Emby at {url} {error}")
            return False

    ##############################################################################
    # Public functions
    ##############################################################################

    def test_notify(self, host, emby_apikey):
        return self._notify_emby("This is a test notification from SickChill", host, emby_apikey)

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        if settings.USE_EMBY:
            if not settings.EMBY_HOST:
                logger.debug("EMBY: No host specified, check your settings")
                return False

            params = {}
            if show:
                params.update({"TvdbId": show.indexerid})
                # Endpoint emby/Library/Series/Added is deprecated http://swagger.emby.media/?staticview=true#/LibraryService/postLibrarySeriesAdded
                url = urljoin(settings.EMBY_HOST, "emby/Library/Series/Added")
            else:
                url = urljoin(settings.EMBY_HOST, "emby/Library/Refresh")

            try:
                session = self.__make_session()
                response = session.post(url, params=params)
                response.raise_for_status()
                logger.debug("EMBY: HTTP status: {0}, response: {1}".format(response.status_code, response.text.replace("\n", "")))
                return True

            except requests.exceptions.RequestException as error:
                logger.warning(f"EMBY: Warning: Could not contact Emby at {url} {error}")

                return False
