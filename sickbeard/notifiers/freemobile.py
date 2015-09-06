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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.
import urllib2

import sickbeard
from sickbeard import logger
from sickbeard.common import notifyStrings, NOTIFY_SNATCH, NOTIFY_DOWNLOAD, NOTIFY_SUBTITLE_DOWNLOAD, NOTIFY_GIT_UPDATE, NOTIFY_GIT_UPDATE_TEXT

class FreeMobileNotifier:
    def test_notify(self, id=None, apiKey=None):
        return self._notifyFreeMobile('Test', "This is a test notification from SickRage", id, apiKey, force=True)

    def _sendFreeMobileSMS(self, title, msg, id=None, apiKey=None):
        """
        Sends a SMS notification
        
        msg: The message to send (unicode)
        title: The title of the message
        userKey: The pushover user id to send the message to (or to subscribe with)
        
        returns: True if the message succeeded, False otherwise
        """

        if id == None:
            id = sickbeard.FREEMOBILE_ID
        if apiKey == None:
            apiKey = sickbeard.FREEMOBILE_APIKEY

        logger.log("Free Mobile in use with API KEY: " + apiKey, logger.DEBUG)

        # build up the URL and parameters
        msg = msg.strip()
        msg_quoted = urllib2.quote(title.encode('utf-8') + ": " + msg.encode('utf-8'))
        URL = "https://smsapi.free-mobile.fr/sendmsg?user=" + id + "&pass=" + apiKey + "&msg=" + msg_quoted
        
        req = urllib2.Request(URL)
        # send the request to Free Mobile
        try:
            reponse = urllib2.urlopen(req)
        except IOError, e:
            if hasattr(e,'code'):
                if e.code == 400:
                    message = "Missing parameter(s)."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 402:
                    message = "Too much SMS sent in a short time."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 403:
                    message = "API service isn't enabled in your account or ID / API key is incorrect."
                    logger.log(message, logger.ERROR)
                    return False, message
                if e.code == 500:
                    message = "Server error. Please retry in few moment."
                    logger.log(message, logger.ERROR)
                    return False, message
        except Exception, e:
                message = u"Error while sending SMS: {0}".format(e)
                logger.log(message, logger.ERROR)
                return False, message

        message = "Free Mobile SMS successful."
        logger.log(message, logger.INFO)
        return True, message
     



    def notify_snatch(self, ep_name, title=notifyStrings[NOTIFY_SNATCH]):
        if sickbeard.FREEMOBILE_NOTIFY_ONSNATCH:
            self._notifyFreeMobile(title, ep_name)


    def notify_download(self, ep_name, title=notifyStrings[NOTIFY_DOWNLOAD]):
        if sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD:
            self._notifyFreeMobile(title, ep_name)

    def notify_subtitle_download(self, ep_name, lang, title=notifyStrings[NOTIFY_SUBTITLE_DOWNLOAD]):
        if sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notifyFreeMobile(title, ep_name + ": " + lang)
            
    def notify_git_update(self, new_version = "??"):
        if sickbeard.USE_FREEMOBILE:
            update_text=notifyStrings[NOTIFY_GIT_UPDATE_TEXT]
            title=notifyStrings[NOTIFY_GIT_UPDATE]
            self._notifyFreeMobile(title, update_text + new_version) 

    def _notifyFreeMobile(self, title, message, id=None, apiKey=None, force=False):
        """
        Sends a SMS notification

        title: The title of the notification to send
        message: The message string to send
        id: Your Free Mobile customer ID
        apikey: Your Free Mobile API key
        force: Enforce sending, for instance for testing
        """

        if not sickbeard.USE_FREEMOBILE and not force:
            logger.log("Notification for Free Mobile not enabled, skipping this notification", logger.DEBUG)
            return False

        logger.log("Sending a SMS for " + message, logger.DEBUG)

        return self._sendFreeMobileSMS(title, message, id, apiKey)


notifier = FreeMobileNotifier
