import json
import time

import certifi
import requests
from requests.exceptions import RequestException
from requests.structures import CaseInsensitiveDict

from sickchill import logger, settings

from .exceptions import traktException


class TraktAPI:
    def __init__(self, ssl_verify=True, timeout=30):
        self.verify = certifi.where() if ssl_verify else False
        self.timeout = timeout if timeout else None
        self.auth_url = settings.TRAKT_OAUTH_URL
        self.api_url = settings.TRAKT_API_URL
        self.headers = CaseInsensitiveDict({"Content-Type": "application/json", "trakt-api-version": "2", "trakt-api-key": settings.TRAKT_API_KEY})

    def traktToken(self, trakt_pin=None, refresh=False, count=0):

        if count > 3:
            settings.TRAKT_ACCESS_TOKEN = ""
            return False
        elif count > 0:
            time.sleep(2)

        data = {"client_id": settings.TRAKT_API_KEY, "client_secret": settings.TRAKT_API_SECRET, "redirect_uri": "urn:ietf:wg:oauth:2.0:oob"}

        if refresh:
            data["grant_type"] = "refresh_token"
            data["refresh_token"] = settings.TRAKT_REFRESH_TOKEN
        else:
            data["grant_type"] = "authorization_code"
            if trakt_pin:
                data["code"] = trakt_pin

        headers = CaseInsensitiveDict({"Content-Type": "application/json"})

        resp = self.traktRequest("oauth/token", data=data, headers=headers, url=self.auth_url, method="POST", count=count)

        if "access_token" in resp:
            settings.TRAKT_ACCESS_TOKEN = resp["access_token"]
            if "refresh_token" in resp:
                settings.TRAKT_REFRESH_TOKEN = resp["refresh_token"]
            return True
        return False

    def validateAccount(self):

        resp = self.traktRequest("users/settings")

        if "account" in resp:
            return True
        return False

    def traktRequest(self, path, data=None, headers=None, url=None, method="GET", count=0):
        if url is None:
            url = self.api_url

        count = count + 1

        if headers is None:
            headers = self.headers

        if settings.TRAKT_ACCESS_TOKEN == "" and count >= 2:
            logger.warning(_("You must get a Trakt TOKEN. Check your Trakt settings"))
            return {}

        if settings.TRAKT_ACCESS_TOKEN != "":
            headers["Authorization"] = "Bearer " + settings.TRAKT_ACCESS_TOKEN

        try:
            resp = requests.request(method, url + path, headers=headers, timeout=self.timeout, data=json.dumps(data) if data else [], verify=self.verify)

            # check for http errors and raise if any are present
            resp.raise_for_status()

            # convert response to json
            resp = resp.json()
        except RequestException as error:
            code = getattr(error.response, "status_code", None)
            if not code:
                if "timed out" in error:
                    logger.warning(_("Timeout connecting to Trakt. Try to increase timeout value in Trakt settings"))
                # This is pretty much a fatal error if there is no status_code
                # It means there basically was no response at all
                else:
                    logger.debug(_(f"Could not connect to Trakt. Error: {error}"))
            elif code == 502:
                # Retry the request, cloudflare had a proxying issue
                logger.debug(_(f"Retrying trakt api request: {path}"))
                return self.traktRequest(path, data, headers, url, method)
            elif code == 401:
                if self.traktToken(refresh=True, count=count):
                    return self.traktRequest(path, data, headers, url, method)
                else:
                    logger.warning("Unauthorized. Please check your Trakt settings")
            elif code in (500, 501, 503, 504, 520, 521, 522):
                # http://docs.trakt.apiary.io/#introduction/status-codes
                logger.debug(_("Trakt may have some issues and it's unavailable. Try again later please"))
            elif code == 404:
                logger.debug(_(f"Trakt error (404) the resource does not exist: {url}{path}"))
            else:
                logger.exception(_(f"Could not connect to Trakt. Code error: {code}"))
            return {}

        # check and confirm trakt call did not fail
        if isinstance(resp, dict) and resp.get("status", False) == "failure":
            if "message" in resp:
                raise traktException(resp["message"])
            if "error" in resp:
                raise traktException(resp["error"])
            else:
                raise traktException("Unknown Error")

        return resp
