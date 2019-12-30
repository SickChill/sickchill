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

import sickbeard
from sickbeard import logger, ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Manage

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/manage/manageSearches(/?.*)', name='manage:searches')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="manage_manageSearches.mako")
        # t.backlogPI = sickbeard.backlogSearchScheduler.action.getProgressIndicator()

        return t.render(backlogPaused=sickbeard.searchQueueScheduler.action.is_backlog_paused(),
                        backlogRunning=sickbeard.searchQueueScheduler.action.is_backlog_in_progress(),
                        dailySearchStatus=sickbeard.dailySearchScheduler.action.amActive,
                        findPropersStatus=sickbeard.properFinderScheduler.action.amActive,
                        queueLength=sickbeard.searchQueueScheduler.action.queue_length(),
                        subtitlesFinderStatus=sickbeard.subtitlesFinderScheduler.action.amActive,
                        title=_('Manage Searches'), header=_('Manage Searches'), topmenu='manage',
                        controller="manage", action="manageSearches")

    def forceBacklog(self):
        # force it to run the next time it looks
        result = sickbeard.backlogSearchScheduler.forceRun()
        if result:
            logger.log("Backlog search forced")
            ui.notifications.message(_('Backlog search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):

        # force it to run the next time it looks
        result = sickbeard.dailySearchScheduler.forceRun()
        if result:
            logger.log("Daily search forced")
            ui.notifications.message(_('Daily search started'))

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        result = sickbeard.properFinderScheduler.forceRun()
        if result:
            logger.log("Find propers search forced")
            ui.notifications.message(_('Find propers search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSubtitlesFinder(self):
        # force it to run the next time it looks
        result = sickbeard.subtitlesFinderScheduler.forceRun()
        if result:
            logger.log("Subtitle search forced")
            ui.notifications.message(_('Subtitle search started'))

        return self.redirect("/manage/manageSearches/")

    def pauseBacklog(self, paused=None):
        if paused == "1":
            sickbeard.searchQueueScheduler.action.pause_backlog()
        else:
            sickbeard.searchQueueScheduler.action.unpause_backlog()

        return self.redirect("/manage/manageSearches/")
