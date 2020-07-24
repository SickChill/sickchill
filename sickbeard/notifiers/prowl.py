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
#
##############################################################################
# Stdlib Imports
import ast
import socket
import time
from http.client import HTTPException, HTTPSConnection
from ssl import SSLError

# Third Party Imports
from requests.compat import urlencode

# First Party Imports
import sickbeard
from sickbeard import common, db, logger
from sickchill import settings


class Notifier(object):
    def test_notify(self, prowl_api, prowl_priority):
        return self._send_prowl(prowl_api, prowl_priority, event="Test", message="Testing Prowl settings from SickChill", force=True)

    def notify_snatch(self, ep_name):
        if settings.PROWL_NOTIFY_ONSNATCH:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.debug('Skipping prowl notify because there are no configured recipients')
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_SNATCH],
                                     message=ep_name + " :: " + time.strftime(settings.DATE_PRESET + " " + settings.TIME_PRESET))

    def notify_download(self, ep_name):
        if settings.PROWL_NOTIFY_ONDOWNLOAD:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.debug('Skipping prowl notify because there are no configured recipients')
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                                     message=ep_name + " :: " + time.strftime(settings.DATE_PRESET + " " + settings.TIME_PRESET))

    def notify_subtitle_download(self, ep_name, lang):
        if settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.debug('Skipping prowl notify because there are no configured recipients')
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                                     message=ep_name + " [" + lang + "] :: " + time.strftime(
                                         settings.DATE_PRESET + " " + settings.TIME_PRESET))

    def notify_git_update(self, new_version="??"):
        if settings.USE_PROWL:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._send_prowl(prowl_api=None, prowl_priority=None,
                             event=title, message=update_text + new_version)

    def notify_login(self, ipaddress=""):
        if settings.USE_PROWL:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_prowl(prowl_api=None, prowl_priority=None,
                             event=title, message=update_text.format(ipaddress))

    @staticmethod
    def _generate_recipients(show=None):
        apis = []
        mydb = db.DBConnection(row_type='dict')

        # Grab the global recipient(s)
        if settings.PROWL_API:
            for api in settings.PROWL_API.split(','):
                if api.strip():
                    apis.append(api.strip())

        # Grab the per-show-notification recipients
        if show is not None:
            for value in show:
                for subs in mydb.select("SELECT notify_list FROM tv_shows WHERE show_name = ?", (value,)):
                    if subs['notify_list'] and subs['notify_list'][0] == '{':               # legacy format handling
                        entries = dict(ast.literal_eval(subs['notify_list']))
                        for api in entries['prowlAPIs'].split(','):
                            if api.strip():
                                apis.append(api.strip())

        apis = set(apis)
        return apis

    @staticmethod
    def _send_prowl(prowl_api=None, prowl_priority=None, event=None, message=None, force=False):

        if not settings.USE_PROWL and not force:
            return False

        if prowl_api is None:
            prowl_api = settings.PROWL_API
            if len(prowl_api) == 0:
                return False

        if prowl_priority is None:
            prowl_priority = settings.PROWL_PRIORITY

        title = settings.PROWL_MESSAGE_TITLE

        logger.debug("PROWL: Sending notice with details: title=\"{0}\" event=\"{1}\", message=\"{2}\", priority={3}, api={4}".format(title, event, message, prowl_priority, prowl_api))

        http_handler = HTTPSConnection("api.prowlapp.com")

        data = {'apikey': prowl_api,
                'application': title,
                'event': event,
                'description': message,
                'priority': prowl_priority}

        try:
            http_handler.request("POST",
                                 "/publicapi/add",
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
        except (SSLError, HTTPException, socket.error):
            logger.exception("Prowl notification failed.")
            return False
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
            logger.info("Prowl notifications sent.")
            return True
        elif request_status == 401:
            logger.exception("Prowl auth failed: {0}".format(response.reason))
            return False
        else:
            logger.exception("Prowl notification failed.")
            return False

    @staticmethod
    def _parse_episode(ep_name):
        sep = " - "
        titles = ep_name.split(sep)
        titles.sort(key=len, reverse=True)
        logger.debug("TITLES: {0}".format(titles))
        return titles
