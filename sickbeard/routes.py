# coding=utf-8
# URL: https://sick-rage.github.io
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

from __future__ import unicode_literals

import tornado.web

route_list = []


class route(object):
    _routes = []

    def __init__(self, uri, name=None):
        self._uri = uri
        self.name = name

    def __call__(self, _handler):
        """ Gets called when we decorate a class """
        name = self.name and self.name or _handler.__name__
        self._routes.append((self._uri, _handler, name))
        return _handler

    @classmethod
    def get_routes(cls, webroot=''):
        cls._routes.reverse()
        routes = [tornado.web.url(webroot + _uri, _handler, name=name) for _uri, _handler, name, in cls._routes]
        return routes


def route_redirect(src, dst, name=None):
    route._routes.append(tornado.web.url(src, tornado.web.RedirectHandler, dict(url=dst), name=name))
