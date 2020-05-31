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
import os
import re
import time

# Third Party Imports
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup
from mako.runtime import UNDEFINED
from mako.template import Template
from tornado.escape import linkify

# First Party Imports
import sickbeard
from sickbeard import classes, helpers
from sickchill.helper.encoding import ek

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json

mako_lookup = {}


def get_lookup():
    mako_lookup['mako'] = mako_lookup.get('mako') or TemplateLookup(
        directories=[ek(os.path.join, sickbeard.PROG_DIR, "gui/" + sickbeard.GUI_NAME + "/views/")],
        module_directory=ek(os.path.join, sickbeard.CACHE_DIR, 'mako'),
        strict_undefined=sickbeard.BRANCH and sickbeard.BRANCH != 'master',
        #  format_exceptions=True,
        filesystem_checks=True
    )
    return mako_lookup.get('mako')


class PageTemplate(Template):
    def __init__(self, rh, filename):
        super(PageTemplate, self).__init__(filename)
        self.arguments = {}

        lookup = get_lookup()
        self.template = lookup.get_template(filename)

        self.arguments['srRoot'] = sickbeard.WEB_ROOT
        self.arguments['sbHttpPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsPort'] = sickbeard.WEB_PORT
        self.arguments['sbHttpsEnabled'] = sickbeard.ENABLE_HTTPS
        self.arguments['sbHandleReverseProxy'] = sickbeard.HANDLE_REVERSE_PROXY
        self.arguments['sbDefaultPage'] = sickbeard.DEFAULT_PAGE
        self.arguments['srLogin'] = rh.get_current_user()
        self.arguments['sbStartTime'] = rh.startTime
        self.arguments['static_url'] = rh.static_url
        self.arguments['reverse_url'] = rh.reverse_url
        self.arguments['linkify'] = linkify

        if rh.request.headers['Host'][0] == '[':
            self.arguments['sbHost'] = re.match(r"^\[.*\]", rh.request.headers['Host'], re.X | re.M | re.S).group(0)
        else:
            self.arguments['sbHost'] = re.match(r"^[^:]+", rh.request.headers['Host'], re.X | re.M | re.S).group(0)

        if "X-Forwarded-Host" in rh.request.headers:
            self.arguments['sbHost'] = rh.request.headers['X-Forwarded-Host']
        if "X-Forwarded-Port" in rh.request.headers:
            sbHttpPort = rh.request.headers['X-Forwarded-Port']
            self.arguments['sbHttpsPort'] = sbHttpPort
        if "X-Forwarded-Proto" in rh.request.headers:
            self.arguments['sbHttpsEnabled'] = rh.request.headers['X-Forwarded-Proto'].lower() == 'https'

        self.arguments['numErrors'] = len(classes.ErrorViewer.errors)
        self.arguments['numWarnings'] = len(classes.WarningViewer.errors)
        self.arguments['sbPID'] = str(sickbeard.PID)

        self.arguments['title'] = "FixME"
        self.arguments['header'] = "FixME"
        self.arguments['topmenu'] = "FixME"
        self.arguments['submenu'] = []
        self.arguments['controller'] = "FixME"
        self.arguments['action'] = "FixME"
        self.arguments['show'] = UNDEFINED
        self.arguments['manage_torrents_url'] = helpers.manage_torrents_url()
        self.arguments['get_current_user'] = rh.get_current_user
        self.arguments['remote_ip'] = rh.request.remote_ip

    def render(self, *args, **kwargs):
        for key in self.arguments:
            if key not in kwargs:
                kwargs[key] = self.arguments[key]

        kwargs['makoStartTime'] = time.time()
        # noinspection PyBroadException
        try:
            return self.template.render_unicode(*args, **kwargs)
        except Exception:
            kwargs['title'] = '500'
            kwargs['header'] = _('Mako Error')
            kwargs['backtrace'] = RichTraceback()
            return get_lookup().get_template('500.mako').render_unicode(*args, **kwargs)
