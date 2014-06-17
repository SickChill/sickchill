# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
# Author: Aaron Bieber <deftly@gmail.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib, urllib2
import time

import sickbeard

from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD
from sickbeard.exceptions import ex

API_URL = "https://api.pushover.net/1/messages.json"
API_KEY = "awKfdt263PLaEWV9RXuSn4c46qoAyA"


class PushoverNotifier:
    def test_notify(self, userKey=None, apiKey=None):
        return self._notifyPushover("This is a test notification from SickRage", 'Test', userKey, force=True)

    def _sendPushover(self, msg, title, userKey=None, apiKey=None):
        """
        Sends a pushover notification to the address provided
        
        msg: The message to send (unicode)
        title: The title of the message
        userKey: The pushover user id to send the message to (or to subscribe with)
        
        returns: True if the message succeeded, False otherwise
        """

        if not userKey:
            userKey = sickbeard.PUSHOVER_USERKEY

        if not apiKey:
            apiKey = sickbeard.PUSHOVER_APIKEY or API_KEY

        logger.log("Pushover API KEY in use: " + apiKey, logger.DEBUG)
        
        # build up the URL and parameters
        msg = msg.strip()
        curUrl = API_URL

        data = urllib.urlencode({
            'token': apiKey,
            'title': title,
            'user': userKey,
            'message': msg.encode('utf-8'),
            'timestamp': int(time.time())
        })


        # send the request to pushover
        try:
            req = urllib2.Request(curUrl)
            handle = urllib2.urlopen(req, data)
            handle.close()

        except urllib2.HTTPError, e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            if not hasattr(e, 'code'):
                logger.log("Pushover notification failed." + ex(e), logger.ERROR)
                return False
            else:
                logger.log("Pushover notification failed. Error code: " + str(e.code), logger.ERROR)

            # HTTP status 404 if the provided email address isn't a Pushover user.
            if e.code == 404:
                logger.log("Username is wrong/not a pushover email. Pushover will send an email to it", logger.WARNING)
                return False

            # For HTTP status code 401's, it is because you are passing in either an invalid token, or the user has not added your service.
            elif e.code == 401:

                #HTTP status 401 if the user doesn't have the service added
                subscribeNote = self._sendPushover(msg, title, userKey, apiKey)
                if subscribeNote:
                    logger.log("Subscription send", logger.DEBUG)
                    return True
                else:
                    logger.log("Subscription could not be send", logger.ERROR)
                    return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif e.code == 400:
                logger.log("Wrong data sent to pushover", logger.ERROR)
                return False

        logger.log("Pushover notification successful.", logger.MESSAGE)
        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.PUSHOVER_NOTIFY_ONSNATCH:
            self._notifyPushover(title, ep_name)


    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD:
            self._notifyPushover(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyPushover(title, ep_name + ": " + lang)

    def _notifyPushover(self, title, message, userKey=None, apiKey=None, force=False):
        """
        Sends a pushover notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        userKey: The userKey to send the notification to 
        force: Enforce sending, for instance for testing
        """

        if not sickbeard.USE_PUSHOVER and not force:
            logger.log("Notification for Pushover not enabled, skipping this notification", logger.DEBUG)
            return False

        logger.log("Sending notification for " + message, logger.DEBUG)

        # self._sendPushover(message, title, userKey, apiKey)
        return self._sendPushover(message, title, userKey, apiKey)


notifier = PushoverNotifier
