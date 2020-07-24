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
# Stdlib Imports
import traceback

# Third Party Imports
from tornado.web import RequestHandler

# First Party Imports
import sickbeard
from sickbeard import helpers, logger
from sickchill import settings


class KeyHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super(KeyHandler, self).__init__(*args, **kwargs)

    def get(self):
        if self.get_query_argument('u', None) == settings.WEB_USERNAME and self.get_query_argument('p', None) == settings.WEB_PASSWORD:
            if not len(settings.API_KEY or ''):
                settings.API_KEY = helpers.generateApiKey()
            result = {'success': True, 'api_key': settings.API_KEY}
        else:
            result = {'success': False, 'error': _('Failed authentication while getting api key')}
            logger.warning(_('Authentication failed during api key request: {0}').format((traceback.format_exc())))

        return self.finish(result)
