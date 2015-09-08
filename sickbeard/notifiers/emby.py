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
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import urllib2

import sickbeard

from sickbeard import logger
from sickbeard.exceptions import ex


try:
    import json
except ImportError:
    import simplejson as json

class EMBYNotifier:

    def _notify_emby(self, message, host=None, emby_apikey=None):
        """Handles notifying Emby host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        # fill in omitted parameters
        if not host:
            host = sickbeard.EMBY_HOST
        if not emby_apikey:
            emby_apikey = sickbeard.EMBY_APIKEY

        url = 'http://%s/emby/Notifications/Admin' % (host)
        values = {'Name': 'SickRage', 'Description': message, 'ImageUrl': 'https://raw.githubusercontent.com/SiCKRAGETV/SickRage/master/gui/slick/images/sickrage-shark-mascot.png'}
        data = json.dumps(values)
        try:
            req = urllib2.Request(url, data)
            req.add_header('X-MediaBrowser-Token', emby_apikey)
            req.add_header('Content-Type', 'application/json')

            response = urllib2.urlopen(req)
            result = response.read()
            response.close()

            logger.log(u'EMBY: HTTP response: ' + result.replace('\n', ''), logger.DEBUG)
            return True

        except (urllib2.URLError, IOError), e:
            logger.log(u'EMBY: Warning: Couldn\'t contact Emby at ' + url + ' ' + ex(e), logger.WARNING)
            return False


##############################################################################
# Public functions
##############################################################################

    def test_notify(self, host, emby_apikey):
        return self._notify_emby('This is a test notification from SickRage', host, emby_apikey)

    def update_library(self, show=None):
        """Handles updating the Emby Media Server host via HTTP API

        Returns:
            Returns True for no issue or False if there was an error

        """

        if sickbeard.USE_EMBY:

            if not sickbeard.EMBY_HOST:
                logger.log(u'EMBY: No host specified, check your settings', logger.DEBUG)
                return False

            if show:
                if show.indexer == 1:
                    provider = 'tvdb'
                elif show.indexer == 2:
                    logger.log(u'EMBY: TVRage Provider no longer valid', logger.WARNING)
                    return False
                else:
                    logger.log(u'EMBY: Provider unknown', logger.WARNING)
                    return False
                query = '?%sid=%s' % (provider, show.indexerid)
            else:
                query = ''

            url = 'http://%s/emby/Library/Series/Updated%s' % (sickbeard.EMBY_HOST, query)
            values = {}
            data = urllib.urlencode(values)
            try:
                req = urllib2.Request(url, data)
                req.add_header('X-MediaBrowser-Token', sickbeard.EMBY_APIKEY)

                response = urllib2.urlopen(req)
                result = response.read()
                response.close()

                logger.log(u'EMBY: HTTP response: ' + result.replace('\n', ''), logger.DEBUG)
                return True

            except (urllib2.URLError, IOError), e:
                logger.log(u'EMBY: Warning: Couldn\'t contact Emby at ' + url + ' ' + ex(e), logger.WARNING)
                return False

notifier = EMBYNotifier
