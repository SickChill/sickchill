# coding=utf-8
# Author: Paul Cioanca <paul@cioan.ca>
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

import urlparse

import requests

import sickbeard
from sickbeard import logger
from sickbeard.common import (NOTIFY_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, NOTIFY_LOGIN, NOTIFY_LOGIN_TEXT, NOTIFY_SNATCH,
                              NOTIFY_SUBTITLE_DOWNLOAD, notifyStrings)
from sickrage.helper.exceptions import ex


class Notifier(object):
    def __init__(self):
        pass

    def test_webhook(self, url=None, token=None):
        payload = {
            "message": "This is a test notification from SickRage",
            "title": "Test"
        }

        return self._notifyWebhook(payload, url=url, token=token)

    def _notifyWebhook(self, payload=None, url=None, token=None):
        """
        Sends a POST request to the provided URL in a JSON object format

        payload: dict containing the request payload
        url: The URL to which the request will be sent
        token: Optional authentication token, send as value in the X-SICKRAGE-AUTH header
        returns: True if the message succeeded, False otherwise
        """

        if payload is None:
            payload = {}

        if url is None:
            url = sickbeard.WEBHOOK_POST_URL

        if token is None:
            token = sickbeard.WEBHOOK_POST_TOKEN

        logger.log("Sending Webhook notification to " + url, logger.DEBUG)

        headers = {}
        if token:
            headers['X-SICKRAGE-AUTH'] = token

        status_code = None
        try:
            r = requests.post(url, json=payload, headers=headers)
            status_code = r.status_code
        except requests.RequestException as e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            if not hasattr(e, 'code'):
                logger.log("Webhook notification failed." + ex(e), logger.ERROR)
                return False
            else:
                logger.log("Webhook notification failed. Error code: " + str(e.code), logger.ERROR)

            if isinstance(e, requests.ConnectionError):
                logger.log("There was a connection error to " + url, logger.ERROR)
                return False

            if isinstance(e, requests.URLRequired):
                logger.log("A valid URL is required to make a request", logger.ERROR)
                return False

            if isinstance(e, requests.TooManyRedirects):
                logger.log("Too many redirects", logger.ERROR)
                return False

            if isinstance(e, requests.ConnectTimeout):
                logger.log("Connection timeout", logger.ERROR)
                return False

            if isinstance(e, requests.Timeout):
                logger.log("Request timeout", logger.ERROR)
                return False

            if e.code:
                status_code = e.code

        if status_code and not self._is_valid_status_code(status_code):
            return False

        logger.log("Webhook notification successful.", logger.INFO)
        return True

    def _is_valid_status_code(self, status_code):
        if status_code == 404:
            logger.log("Webhook response returned 404 not found", logger.ERROR)
            return False

        elif status_code == 401:
            logger.log("Unauthorized. Invalid X-SICKRAGE-AUTH token", logger.ERROR)
            return False

        elif status_code == 400:
            logger.log("Wrong data structure sent to webhook URL", logger.ERROR)
            return False

        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.WEBHOOK_NOTIFY_ONSNATCH:
            self._notifyWebhook({
                "title": title,
                "ep_name": ep_name
            })

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.WEBHOOK_NOTIFY_ONDOWNLOAD:
            self._notifyWebhook({
                "title": title,
                "ep_name": ep_name
            })

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.WEBHOOK_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyWebhook({
                "title": title,
                "ep_name": ep_name + ": " + lang
            })

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_WEBHOOK:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyWebhook({
                "title": title,
                "update_text": update_text + new_version
            })

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_WEBHOOK:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notifyWebhook({
                "title": title,
                "update_text": update_text.format(ipaddress)
            })

    def validate_url(self, url=None):
        if not url:
            return False

        parsed_url = urlparse.urlparse(url)
        has_schema = bool(parsed_url.scheme)

        return has_schema
