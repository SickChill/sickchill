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

# Third Party Imports
from tornado.escape import xhtml_unescape

# First Party Imports
from sickbeard.browser import foldersAtPath
from sickchill.helper.encoding import ek

# Local Folder Imports
from .index import WebRoot
from .routes import Route

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/browser(/?.*)', name='filebrowser')
class WebFileBrowser(WebRoot):
    def __init__(self, *args, **kwargs):
        super(WebFileBrowser, self).__init__(*args, **kwargs)

    def index(self, path='', includeFiles=False, fileTypes=''):  # pylint: disable=arguments-differ

        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header(b'Content-Type', 'application/json')

        return json.dumps(foldersAtPath(xhtml_unescape(path), True, bool(int(includeFiles)), fileTypes.split(',')))

    def complete(self, term, includeFiles=False, fileTypes=''):

        self.set_header(b'Cache-Control', 'max-age=0,no-cache,no-store')
        self.set_header(b'Content-Type', 'application/json')
        paths = [entry['path'] for entry in foldersAtPath(ek(os.path.dirname, xhtml_unescape(term)), includeFiles=bool(int(includeFiles)),
                                                          fileTypes=fileTypes.split(','))
                 if 'path' in entry]

        return json.dumps(paths)
