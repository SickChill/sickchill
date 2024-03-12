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

        if not settings.USE_EMBY:
            logger.debug("Notification for Emby not enabled, skipping this notification")
            return False

        try:
            response = requests.post(url, params=params, headers=self._make_headers(emby_apikey))
            if response:
                logger.debug(_("EMBY: HTTP response: {content}").format(content=response.content))
            response.raise_for_status()

            return True
        except RequestException as error:
            logger.warning(_("EMBY: Warning: Could not contact Emby at {url} {error}").format(url=url, error=error))
            return False

    def _get_show_path(self, tvdbid):
        """Get a show path in Emby library using Items endpoint

        Returns:
            The show path in Emby or empty

        """
        get_path_params = {"Recursive": "true", "Fields": "Path", "IncludeItemTypes": "Series"}
        url = urljoin(settings.EMBY_HOST, "/Items")
        try:
            get_path_params.update({"AnyProviderIdEquals": "tvdb.{id}".format(id=tvdbid)})
            items_response = requests.get(url, params=get_path_params, headers=self._make_headers())
            items_response.raise_for_status()
            if items_response.json()["TotalRecordCount"] == 1:
                return items_response.json()["Items"][0]["Path"]
            else:
                return ""

        except requests.exceptions.RequestException as error:
            logger.warning(_("EMBY: Warning: Could not contact Emby at {url} {error}").format(url=url, error=error))
            return None

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
            try:
                if show:
                    path = self._get_show_path(show.indexerid)
                    if path:
                        url = urljoin(settings.EMBY_HOST, "emby/Library/Media/Updated")
                        params.update({"Updates": {"Path": path, "UpdateType": "Created"}})
                    else:
                        url = urljoin(settings.EMBY_HOST, "emby/Library/Refresh")
                else:
                    url = urljoin(settings.EMBY_HOST, "emby/Library/Refresh")

                response = requests.post(url, json=params, headers=self._make_headers())

                response.raise_for_status()
                logger.debug(_("EMBY: HTTP status: {status_code}, response: {content}").format(status_code=response.status_code, content=response.content))
                return True

            except requests.exceptions.RequestException as error:
                logger.warning(_("EMBY: Warning: Could not contact Emby at {url} {error}").format(url=url, error=error))

                return False
