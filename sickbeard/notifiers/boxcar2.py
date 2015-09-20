# Author: Rafael Silva <rpluto@gmail.com>
# Author: Marvin Pinto <me@marvinp.ca>
# Author: Dennis Lutter <lad1337@gmail.com>
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

import sickbeard

from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT
from sickrage.helper.exceptions import ex

API_URL = "https://new.boxcar.io/api/notifications"


class Boxcar2Notifier:
    def test_notify(self, accesstoken, title="SickRage : Test"):
        return self._sendBoxcar2("This is a test notification from SickRage", title, accesstoken)

    def _sendBoxcar2(self, msg, title, accesstoken):
        """
        Sends a boxcar2 notification to the address provided

        msg: The message to send
        title: The title of the message
        accesstoken: to send to this device

        returns: True if the message succeeded, False otherwise
        """

        # build up the URL and parameters
	#more info goes here - https://boxcar.uservoice.com/knowledgebase/articles/306788-how-to-send-your-boxcar-account-a-notification
        msg = msg.strip()
        curUrl = API_URL

        data = urllib.urlencode({
                'user_credentials': accesstoken,
                'notification[title]': "SickRage : " + title + ' : ' + msg,
                'notification[long_message]': msg,
                'notification[sound]': "notifier-2"
            })

        # send the request to boxcar2
        try:
            req = urllib2.Request(curUrl)
            handle = urllib2.urlopen(req, data,timeout=60)
            handle.close()

        except Exception as e:
            # if we get an error back that doesn't have an error code then who knows what's really happening
            if not hasattr(e, 'code'):
                logger.log("Boxcar2 notification failed." + ex(e), logger.ERROR)
                return False
            else:
                logger.log("Boxcar2 notification failed. Error code: " + str(e.code), logger.WARNING)

            # HTTP status 404
            if e.code == 404:
                logger.log("Access token is invalid. Check it.", logger.WARNING)
                return False

            # If you receive an HTTP status code of 400, it is because you failed to send the proper parameters
            elif e.code == 400:
                logger.log("Wrong data send to boxcar2", logger.ERROR)
                return False

        logger.log("Boxcar2 notification successful.", logger.DEBUG)
        return True

    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.BOXCAR2_NOTIFY_ONSNATCH:
            self._notifyBoxcar2(title, ep_name)


    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD:
            self._notifyBoxcar2(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyBoxcar2(title, ep_name + ": " + lang)

    def notify_git_update(self, new_version = "??"):
        if sickbeard.USE_BOXCAR2:
            update_text=notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title=notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyBoxcar2(title, update_text + new_version)

    def _notifyBoxcar2(self, title, message, accesstoken=None):
        """
        Sends a boxcar2 notification based on the provided info or SB config

        title: The title of the notification to send
        message: The message string to send
        accesstoken: to send to this device
        """

        if not sickbeard.USE_BOXCAR2:
            logger.log("Notification for Boxcar2 not enabled, skipping this notification", logger.DEBUG)
            return False

        # if no username was given then use the one from the config
        if not accesstoken:
            accesstoken = sickbeard.BOXCAR2_ACCESSTOKEN

        logger.log("Sending notification for " + message, logger.DEBUG)

        self._sendBoxcar2(message, title, accesstoken)
        return True


notifier = Boxcar2Notifier
