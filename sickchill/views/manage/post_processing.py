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

# Third Party Imports
from tornado.escape import xhtml_unescape
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import config
from sickchill.helper.encoding import ss
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home
from sickchill.views.routes import Route


@Route('/home/postprocess(/?.*)', name='home:postprocess')
class PostProcess(Home):
    def __init__(self, *args, **kwargs):
        super(PostProcess, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="home_postprocess.mako")
        return t.render(title=_('Post Processing'), header=_('Post Processing'), topmenu='home', controller="home", action="postProcess")

    def processEpisode(self, proc_dir=None, nzbName=None, quiet=None, process_method=None, force=None,
                       is_priority=None, delete_on="0", failed="0", proc_type="manual", force_next=False, *args_, **kwargs):

        mode = kwargs.get('type', proc_type)
        process_path = ss(xhtml_unescape(kwargs.get('dir', proc_dir or '') or ''))
        if not process_path:
            return self.redirect("/home/postprocess/")

        release_name = ss(xhtml_unescape(nzbName)) if nzbName else nzbName

        result = sickbeard.postProcessorTaskScheduler.action.add_item(
            process_path, release_name, method=process_method, force=force,
            is_priority=is_priority, delete=delete_on, failed=failed, mode=mode,
            force_next=force_next
        )

        if config.checkbox_to_value(quiet):
            return result

        result = result.replace("\n", "<br>\n")
        return self._genericMessage("Postprocessing results", result)
