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

from __future__ import absolute_import, print_function, unicode_literals

import os

from api import ApiHandler, KeyHandler
from tornado.web import RedirectHandler, StaticFileHandler, url

import sickbeard
from sickbeard.common import ek

from . import CalendarHandler, LoginHandler, LogoutHandler
from .routes import Route


class Urls(object):
    def __init__(self, **options):
        self.options = options

        self.urls = [
                        url(r'{0}/favicon.ico'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, self.options['data_root'], 'images/ico/favicon.ico')}, name='favicon'),

                        url(r'{0}/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, self.options['data_root'], 'images')}, name='images'),

                        url(r'{0}/cache/images/(.*)'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, sickbeard.CACHE_DIR, 'images')}, name='image_cache'),

                        url(r'{0}/css/(.*)'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, self.options['data_root'], 'css')}, name='css'),

                        url(r'{0}/js/(.*)'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, self.options['data_root'], 'js')}, name='js'),

                        url(r'{0}/fonts/(.*)'.format(self.options['web_root']), StaticFileHandler,
                            {"path": ek(os.path.join, self.options['data_root'], 'fonts')}, name='fonts'),

                        # TODO: WTF is this?
                        # url(r'{0}/videos/(.*)'.format(self.options['web_root']), StaticFileHandler,
                        #     {"path": self.video_root}, name='videos'),

                        url(r'{0}(/?.*)'.format(self.options['api_root']), ApiHandler, name='api'),
                        url(r'{0}/getkey(/?.*)'.format(self.options['web_root']), KeyHandler, name='get_api_key'),

                        url(r'{0}/api/builder'.format(self.options['web_root']), RedirectHandler, {"url": self.options['web_root'] + '/apibuilder/'},
                            name='apibuilder'),
                        url(r'{0}/login(/?)'.format(self.options['web_root']), LoginHandler, name='login'),
                        url(r'{0}/logout(/?)'.format(self.options['web_root']), LogoutHandler, name='logout'),

                        url(r'{0}/calendar/?'.format(self.options['web_root']), CalendarHandler, name='calendar')

                        # routes added by @route decorator
                        # Plus naked index with missing web_root prefix
                    ] + Route.get_routes(self.options['web_root'])
                    # + [r for r in Route.get_routes() if r.name == 'index']
