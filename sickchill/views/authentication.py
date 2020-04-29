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

from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import traceback

# Third Party Imports
from tornado.web import RequestHandler

# First Party Imports
import sickbeard
from sickbeard import helpers, logger, notifiers
from sickchill.helper import try_int

# Local Folder Imports
from .common import PageTemplate
from .index import BaseHandler


class LoginHandler(BaseHandler):
    def get(self, *args, **kwargs):

        if self.get_current_user():
            self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')
        else:
            t = PageTemplate(rh=self, filename="login.mako")
            self.finish(t.render(title=_("Login"), header=_("Login"), topmenu="login"))

    def post(self):
        notifiers.notify_login(self.request.remote_ip)

        if self.get_body_argument('username', None) == sickbeard.WEB_USERNAME and self.get_body_argument('password', None) == sickbeard.WEB_PASSWORD:
            remember_me = (None, 30)[try_int(self.get_body_argument('remember_me'), 0) > 0]
            self.set_secure_cookie('sickchill_user', sickbeard.API_KEY, expires_days=remember_me)
            logger.log('User logged into the SickChill web interface', logger.INFO)
        else:
            logger.log('User attempted a failed login to the SickChill web interface from IP: ' + self.request.remote_ip, logger.WARNING)

        self.redirect('/' + sickbeard.DEFAULT_PAGE + '/')


class LogoutHandler(BaseHandler):
    def get(self, *args, **kwargs):
        self.clear_cookie("sickchill_user")
        self.redirect('/login/')
