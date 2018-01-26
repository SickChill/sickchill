# coding=utf-8
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
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

import time

import requests
import sickbeard
from sickbeard import db, logger
from sickbeard.common import (NOTIFY_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT, NOTIFY_LOGIN, NOTIFY_LOGIN_TEXT, NOTIFY_SNATCH,
                              NOTIFY_SUBTITLE_DOWNLOAD, notifyStrings)
from sickrage.helper.encoding import ss
from sickrage.helper.exceptions import ex
from sickrage.media.ShowBanner import ShowBanner
import traceback

API_URL = "https://api.pushover.net/1/messages.json"


class Notifier(object):
    def __init__(self):
        pass

    def test_notify(self, userKey=None, apiKey=None):
        return self._notifyPushover("This is a test notification from SickRage", 'Test', userKey=userKey, apiKey=apiKey, force=True, attachment="gui/slick/images/banner.png")

    def _sendPushover(self, msg, title, sound=None, userKey=None, apiKey=None, priority=None, attachment=None):
        """
        Sends a pushover notification to the address provided

        msg: The message to send (six.text_type)
        title: The title of the message
        sound: The notification sound to use
        userKey: The pushover user id to send the message to (or to subscribe with)
        apiKey: The pushover api key to use
        attachment: Image attachment
        returns: True if the message succeeded, False otherwise
        """

        if userKey is None:
            userKey = sickbeard.PUSHOVER_USERKEY

        if apiKey is None:
            apiKey = sickbeard.PUSHOVER_APIKEY

        if sound is None:
            sound = sickbeard.PUSHOVER_SOUND

        if priority is None:
            priority = sickbeard.PUSHOVER_PRIORITY

        logger.log("Pushover API KEY in use: " + apiKey, logger.DEBUG)

        # build up the URL and parameters
        msg = msg.strip()

        # send the request to pushover
        try:
            args = {
                "token": apiKey,
                "user": userKey,
                "title": title.encode('utf-8'),
                "message": msg.encode('utf-8'),
                "timestamp": int(time.time()),
                "retry": 60,
                "expire": 3600,
                "priority": priority,
            }
            if sickbeard.PUSHOVER_SOUND != "default":
                args["sound"] = sound
            if sickbeard.PUSHOVER_DEVICE:
                args["device"] = sickbeard.PUSHOVER_DEVICE

            files=None
            if attachment is not None:
                files = {
                    "attachment": open(attachment, 'rb')
                }
            response = requests.post(API_URL, data=args, files=files)

            # HTTP status 404 if the provided email address isn't a Pushover user.
            if response.status_code == 404:
                logger.log("Username is wrong/not a pushover email. Pushover will send an email to it", logger.WARNING)
                return False

            # For HTTP status code 401's, it is because you are passing in either an invalid token, or the user has not added your service.
            elif response.status_code == 401:

                # HTTP status 401 if the user doesn't have the service added
                subscribeNote = self._sendPushover(msg, title, sound=sound, userKey=userKey, apiKey=apiKey)
                if subscribeNote:
                    logger.log("Subscription sent", logger.DEBUG)
                    return True
                else:
                    logger.log("Subscription could not be sent", logger.ERROR)
                    return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif response.status_code == 400:
                logger.log("Wrong data sent to pushover", logger.ERROR)
                return False

            # If you receive a HTTP status code of 429, it is because the message limit has been reached (free limit is 7,500)
            elif response.status_code == 429:
                logger.log("Pushover API message limit reached - try a different API key", logger.ERROR)
                return False

        except requests.exceptions.RequestException as e:
            logger.log("Pushover notification failed." + ex(e), logger.ERROR)
            return False


        logger.log("Pushover notification successful.", logger.INFO)
        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.PUSHOVER_NOTIFY_ONSNATCH:
            attachment = self._get_show_banner(ep_name)
            self._notifyPushover(title, ep_name, attachment=attachment)

    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD:
            attachment = self._get_show_banner(ep_name)
            self._notifyPushover(title, ep_name, attachment=attachment)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD:
            attachment = self._get_show_banner(ep_name)
            self._notifyPushover(title, ep_name + ": " + lang, attachment=attachment)

    def notify_git_update(self, new_version="??"):
        if sickbeard.USE_PUSHOVER:
            update_text = notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title = notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyPushover(title, update_text + new_version)

    def notify_login(self, ipaddress=""):
        if sickbeard.USE_PUSHOVER:
            update_text = notifyStrings[NOTIFY_LOGIN_TEXT]
            title = notifyStrings[NOTIFY_LOGIN]
            self._notifyPushover(title, update_text.format(ipaddress))

    def _notifyPushover(self, title, message, sound=None, userKey=None, apiKey=None, force=False, attachment=None):
        """
        Sends a pushover notification based on the provided info or SR config

        title: The title of the notification to send
        message: The message string to send
        sound: The notification sound to use
        userKey: The userKey to send the notification to
        apiKey: The apiKey to use to send the notification
        force: Enforce sending, for instance for testing
        """

        if not sickbeard.USE_PUSHOVER and not force:
            logger.log("Notification for Pushover not enabled, skipping this notification", logger.DEBUG)
            return False

        logger.log("Sending notification for " + message, logger.DEBUG)

        return self._sendPushover(message, title, sound=sound, userKey=userKey, apiKey=apiKey, attachment=attachment)


    @staticmethod
    def _get_show_banner(ep_name):
        parts = ss(ep_name).split(" - ")
        if len(parts) < 1:
            return None

        mydb = db.DBConnection()
        show_name = parts[0]
        rows = mydb.select('SELECT indexer_id FROM tv_shows WHERE show_name = ?;', [show_name])
        try:
            indexer_id =  rows[0][b'indexer_id']
            return ShowBanner(indexer_id).get_media_path()
        except Exception as error:  # pylint: disable=broad-except
            logger.log('There was an error creating the show: Error {0}'.format(error), logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)
            return None
