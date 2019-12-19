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
# pylint: disable=abstract-method,too-many-lines, R

from __future__ import print_function, unicode_literals

import traceback

from common import PageTemplate
from index import BaseHandler
from tornado.web import RequestHandler

import sickbeard
from sickbeard import helpers, logger, notifiers
from sickchill.helper import try_int

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):

        if self.get_current_user():
            self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')
        else:
            t = PageTemplate(rh=self, filename="login.mako")
            self.finish(t.render(title=_("Login"), header=_("Login"), topmenu="login"))

    def post(self, *args, **kwargs):
        notifiers.notify_login(self.request.remote_ip)

        if self.get_argument('username', '') == sickbeard.WEB_USERNAME and self.get_argument('password', '') == sickbeard.WEB_PASSWORD:
            remember_me = (None, 30)[try_int(self.get_argument('remember_me', default=0), 0) > 0]
            self.set_secure_cookie('sickchill_user', sickbeard.API_KEY, expires_days=remember_me)
            logger.log('User logged into the SickChill web interface', logger.INFO)
        else:
            logger.log('User attempted a failed login to the SickChill web interface from IP: ' + self.request.remote_ip, logger.WARNING)

        self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.clear_cookie("sickchill_user")
        self.redirect('/login/')


class KeyHandler(RequestHandler):
    def data_received(self, chunk):
        pass

    def __init__(self, *args, **kwargs):
        super(KeyHandler, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        if self.get_argument('u', '') == sickbeard.WEB_USERNAME and self.get_argument('p', '') == sickbeard.WEB_PASSWORD:
            if not len(sickbeard.API_KEY or ''):
                sickbeard.API_KEY = helpers.generateApiKey()
            result = {'success': True, 'api_key': sickbeard.API_KEY}
        else:
            result = {'success': False, 'error': _('Failed authentication while getting api key')}
            logger.log(_('Authentication failed during api key request: {0}').format((traceback.format_exc())), logger.WARNING)

        return self.finish(result)
