from urllib.parse import urljoin

import requests
from requests import RequestException
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings


class Notifier(object):
    def _make_headers(self, emby_apikey=None):
        return CaseInsensitiveDict({"X-Emby-Token": emby_apikey or settings.EMBY_APIKEY, "Content-Type": "application/json"})

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """
        url = urljoin(host or settings.EMBY_HOST, "emby/Notifications/Admin")
        params = {"Name": "SickChill", "Description": message, "ImageUrl": settings.LOGO_URL}

        try:
            response = requests.get(url, params=params, headers=self._make_headers(emby_apikey))
            if response:
                logger.debug(_("EMBY: HTTP response: {content}").format(content=response.content))
            response.raise_for_status()

            return True
        except RequestException as error:
            logger.warning(_("EMBY: Warning: Could not contact Emby at {url} {error}").format(url=url, error=error))
            return False

    ##############################################################################
    # Public functions
    ##############################################################################

    def test_notify(self, host, emby_apikey):
        return self._notify_emby(_("This is a test notification from SickChill"), host, emby_apikey)

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        if settings.USE_EMBY:
            if not settings.EMBY_HOST:
                logger.debug(_("EMBY: No host specified, check your settings"))
                return False

            params = {}
            if show:
                params.update({"TvdbId": show.indexerid})
                # Endpoint emby/Library/Series/Added is deprecated http://swagger.emby.media/?staticview=true#/LibraryService/postLibrarySeriesAdded
                url = urljoin(settings.EMBY_HOST, "emby/Library/Series/Added")
            else:
                url = urljoin(settings.EMBY_HOST, "emby/Library/Refresh")

            try:
                response = requests.post(url, params=params, headers=self._make_headers())
                response.raise_for_status()
                logger.debug(_("EMBY: HTTP status: {status_code}, response: {content}").format(status_code=response.status_code, content=response.content))
                return True

            except requests.exceptions.RequestException as error:
                logger.warning(_("EMBY: Warning: Could not contact Emby at {url} {error}").format(url=url, error=error))

                return False
