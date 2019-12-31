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

# Future Imports
from __future__ import absolute_import, print_function, unicode_literals

# Third Party Imports
import markdown2

# First Party Imports
from sickbeard import helpers, logger

# Local Folder Imports
from .common import PageTemplate
from .home import Home
from .routes import Route

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/changes(/?.*)', name='changelog')
class HomeChangeLog(Home):
    def __init__(self, *args, **kwargs):
        super(HomeChangeLog, self).__init__(*args, **kwargs)

    def index(self, *args, **kwargs):
        # noinspection PyBroadException
        try:
            changes = helpers.getURL('http://sickchill.github.io/sickchill-news/CHANGES.md', session=helpers.make_session(), returns='text')
        except Exception:
            logger.log('Could not load changes from repo, giving a link!', logger.DEBUG)
            changes = _('Could not load changes from the repo. [Click here for CHANGES.md]({changes_url})').format(
                changes_url='http://sickchill.github.io/sickchill-news/CHANGES.md'
            )

        t = PageTemplate(rh=self, filename="markdown.mako")
        data = markdown2.markdown(changes if changes else _("The was a problem connecting to github, please refresh and try again"), extras=['header-ids'])

        return t.render(title=_("Changelog"), header=_("Changelog"), topmenu="system", data=data, controller="changes", action="index")
