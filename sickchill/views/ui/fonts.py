# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
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

from __future__ import print_function, unicode_literals

import mimetypes

from tornado.web import StaticFileHandler


class CustomStaticFileHandler(StaticFileHandler):
    """
        Override default StaticFileHandler for misconfigured systems where mimetypes do not work fully or at all
        Adding mimetypes elsewhere works but this makes it obvious why they are added in.
    """

    mimetypes.add_type("application/font-sfnt", ".ttf")
    mimetypes.add_type("application/vnd.ms-fontobject", ".eot")
    mimetypes.add_type("application/font-sfnt", ".otf")
    mimetypes.add_type("application/font-woff", ".woff")
    mimetypes.add_type("application/font-woff2", ".woff2")

    mimetypes.add_type("text/css", ".css")
    mimetypes.add_type("application/javascript", ".js")
    mimetypes.add_type("application/manifest+json", '.webmanifest')
    mimetypes.add_type("application/json", '.json')
    mimetypes.add_type("text/plain", ".txt")
    mimetypes.add_type("application/xml", ".xml")

    mimetypes.add_type("image/vnd.microsoft.icon", ".ico")
    mimetypes.add_type("image/svg+xml", ".svg")
    mimetypes.add_type("image/jpeg", ".jpg")
    mimetypes.add_type("image/gif", ".gif")
    mimetypes.add_type("image/png", ".png")
