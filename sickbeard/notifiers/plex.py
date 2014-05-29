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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import urllib2
import base64

import sickbeard

from sickbeard import logger
from sickbeard import common
from sickbeard.exceptions import ex
from sickbeard.encodingKludge import fixStupidEncodings

from sickbeard.notifiers.xbmc import XBMCNotifier

# TODO: switch over to using ElementTree
from xml.dom import minidom


class PLEXNotifier(XBMCNotifier):
    def _notify_pmc(self, message, title="SickRage", host=None, username=None, password=None, force=False):
          # fill in omitted parameters
        if not host:
            if sickbeard.PLEX_HOST:
                host = sickbeard.PLEX_HOST # Use the default Plex host
            else:
                logger.log(u"No Plex host specified, check your settings", logger.DEBUG)
                return False
        if not username:
            username = sickbeard.PLEX_USERNAME
        if not password:
            password = sickbeard.PLEX_PASSWORD

        # suppress notifications if the notifier is disabled but the notify options are checked
        if not sickbeard.USE_PLEX and not force:
            logger.log("Notification for Plex not enabled, skipping this notification", logger.DEBUG)
            return False

        return self._notify_xbmc(message=message, title=title, host=host, username=username, password=password, force=True)

    def notify_snatch(self, ep_name):
        if sickbeard.PLEX_NOTIFY_ONSNATCH:
            self._notify_pmc(ep_name, common.notifyStrings[common.NOTIFY_SNATCH])

    def notify_download(self, ep_name):
        if sickbeard.PLEX_NOTIFY_ONDOWNLOAD:
            self._notify_pmc(ep_name, common.notifyStrings[common.NOTIFY_DOWNLOAD])

    def notify_subtitle_download(self, ep_name, lang):
        if sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD:
            self._notify_pmc(ep_name + ": " + lang, common.notifyStrings[common.NOTIFY_SUBTITLE_DOWNLOAD])

    def test_notify(self, host, username, password):
        return self._notify_pmc("Testing Plex notifications from SickRage", "Test Notification", host, username,
                                password, force=True)

    def update_library(self):
        """Handles updating the Plex Media Server host via HTTP API

        Plex Media Server currently only supports updating the whole video library and not a specific path.

        Returns:
            Returns True or False

        """

        if sickbeard.USE_PLEX and sickbeard.PLEX_UPDATE_LIBRARY:
            if not sickbeard.PLEX_SERVER_HOST:
                logger.log(u"No Plex Media Server host specified, check your settings", logger.DEBUG)
                return False

            logger.log(u"Updating library for the Plex Media Server host: " + sickbeard.PLEX_SERVER_HOST,
                       logger.MESSAGE)

            url = "http://%s/library/sections" % sickbeard.PLEX_SERVER_HOST
            try:
                xml_sections = minidom.parse(urllib.urlopen(url))
            except IOError, e:
                logger.log(u"Error while trying to contact Plex Media Server: " + ex(e), logger.ERROR)
                return False

            sections = xml_sections.getElementsByTagName('Directory')
            if not sections:
                logger.log(u"Plex Media Server not running on: " + sickbeard.PLEX_SERVER_HOST, logger.MESSAGE)
                return False

            for s in sections:
                if s.getAttribute('type') == "show":
                    url = "http://%s/library/sections/%s/refresh" % (sickbeard.PLEX_SERVER_HOST, s.getAttribute('key'))
                    try:
                        urllib.urlopen(url)
                    except Exception, e:
                        logger.log(u"Error updating library section for Plex Media Server: " + ex(e), logger.ERROR)
                        return False

            return True

notifier = PLEXNotifier
