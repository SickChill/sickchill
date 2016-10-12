# coding=utf-8

# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
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
#
##############################################################################

import socket
from httplib import HTTPSConnection, HTTPException
from requests.compat import urlencode

try:
    # this only exists in 2.6
    from ssl import SSLError
except ImportError:
    # make a fake one since I don't know what it is supposed to be in 2.5
    class SSLError(Exception):
        pass

import sickbeard
import time
import ast

from sickbeard import logger, common, db
from sickrage.helper.encoding import ss


class Notifier(object):
    def test_notify(self, prowl_api, prowl_priority):
        return self._send_prowl(prowl_api, prowl_priority, event="Test", message="Testing Prowl settings from SickRage", force=True)

    def notify_snatch(self, ep_name):
        ep_name = ss(ep_name)
        if sickbeard.PROWL_NOTIFY_ONSNATCH:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.log('Skipping prowl notify because there are no configured recipients', logger.DEBUG)
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_SNATCH],
                                     message=ep_name + " :: " + time.strftime(sickbeard.DATE_PRESET + " " + sickbeard.TIME_PRESET))

    def notify_download(self, ep_name):
        ep_name = ss(ep_name)
        if sickbeard.PROWL_NOTIFY_ONDOWNLOAD:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.log('Skipping prowl notify because there are no configured recipients', logger.DEBUG)
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_DOWNLOAD],
                                     message=ep_name + " :: " + time.strftime(sickbeard.DATE_PRESET + " " + sickbeard.TIME_PRESET))

    def notify_subtitle_download(self, ep_name, lang):
        ep_name = ss(ep_name)
        if sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD:
            show = self._parse_episode(ep_name)
            recipients = self._generate_recipients(show)
            if not recipients:
                logger.log('Skipping prowl notify because there are no configured recipients', logger.DEBUG)
            else:
                for api in recipients:
                    self._send_prowl(prowl_api=api, prowl_priority=None, event=common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD],
                                     message=ep_name + " [" + lang + "] :: " + time.strftime(sickbeard.DATE_PRESET + " " + sickbeard.TIME_PRESET))

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_PROWL:
            update_text = common.notifyStrings[common.NOTIFY_GIT_UPDATE_TEXT]
            title = common.notifyStrings[common.NOTIFY_GIT_UPDATE]
            self._send_prowl(prowl_api=None, prowl_priority=None,
                             event=title, message=update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_PROWL:
            update_text = common.notifyStrings[common.NOTIFY_LOGIN_TEXT]
            title = common.notifyStrings[common.NOTIFY_LOGIN]
            self._send_prowl(prowl_api=None, prowl_priority=None,
                             event=title, message=update_text.format(ipaddress))

    @staticmethod
    def _generate_recipients(show=None):
        apis = []
        mydb = db.DBConnection()

        # Grab the global recipient(s)
        if sickbeard.PROWL_API:
            for api in sickbeard.PROWL_API.split(','):
                if len(api.strip()) > 0:
                    apis.append(api)

        # Grab the per-show-notification recipients
        if show is not None:
            for value in show:
                for subs in mydb.select("SELECT notify_list FROM tv_shows WHERE show_name = ?", (value,)):
                    if subs['notify_list'] and subs['notify_list'][0] == '{':               # legacy format handling
                        entries = dict(ast.literal_eval(subs['notify_list']))
                        for api in entries['prowlAPIs'].split(','):
                            if len(api.strip()) > 0:
                                apis.append(api)

        apis = set(apis)
        return apis

    @staticmethod
    def _send_prowl(prowl_api=None, prowl_priority=None, event=None, message=None, force=False):

        if not sickbeard.USE_PROWL and not force:
            return False

        if prowl_api is None:
            prowl_api = sickbeard.PROWL_API
            if len(prowl_api) == 0:
                return False

        if prowl_priority is None:
            prowl_priority = sickbeard.PROWL_PRIORITY

        title = sickbeard.PROWL_MESSAGE_TITLE

        logger.log(u"PROWL: Sending notice with details: title=\"{0}\" event=\"{1}\", message=\"{2}\", priority={3}, api={4}".format(title, event, message, prowl_priority, prowl_api), logger.DEBUG)

        http_handler = HTTPSConnection("api.prowlapp.com")

        data = {'apikey': prowl_api,
                'application': title,
                'event': event,
                'description': message.encode('utf-8'),
                'priority': prowl_priority}

        try:
            http_handler.request("POST",
                                 "/publicapi/add",
                                 headers={'Content-type': "application/x-www-form-urlencoded"},
                                 body=urlencode(data))
        except (SSLError, HTTPException, socket.error):
            logger.log(u"Prowl notification failed.", logger.ERROR)
            return False
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
            logger.log(u"Prowl notifications sent.", logger.INFO)
            return True
        elif request_status == 401:
            logger.log(u"Prowl auth failed: {0}".format(response.reason), logger.ERROR)
            return False
        else:
            logger.log(u"Prowl notification failed.", logger.ERROR)
            return False

    @staticmethod
    def _parse_episode(ep_name):
        ep_name = ss(ep_name)

        sep = " - "
        titles = ep_name.split(sep)
        titles.sort(key=len, reverse=True)
        logger.log("TITLES: {0}".format(titles), logger.DEBUG)
        return titles
