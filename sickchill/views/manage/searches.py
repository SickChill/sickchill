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
# First Party Imports
from sickbeard import logger, ui
from sickchill import settings
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from . import Manage


@Route('/manage/manageSearches(/?.*)', name='manage:searches')
class ManageSearches(Manage):
    def __init__(self, *args, **kwargs):
        super(ManageSearches, self).__init__(*args, **kwargs)

    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="manage_manageSearches.mako")
        # t.backlogPI = sickbeard.backlogSearchScheduler.action.getProgressIndicator()

        return t.render(backlogPaused=settings.searchQueueScheduler.action.is_backlog_paused(),
                        backlogRunning=settings.searchQueueScheduler.action.is_backlog_in_progress(),
                        dailySearchStatus=settings.dailySearchScheduler.action.amActive,
                        findPropersStatus=settings.properFinderScheduler.action.amActive,
                        subtitlesFinderStatus=settings.subtitlesFinderScheduler.action.amActive,
                        autoPostProcessorStatus=settings.autoPostProcessorScheduler.action.amActive,
                        queueLength=settings.searchQueueScheduler.action.queue_length(),
                        processing_queue=settings.postProcessorTaskScheduler.action.queue_length(),
                        title=_('Manage Searches'), header=_('Manage Searches'), topmenu='manage',
                        controller="manage", action="manageSearches")

    def forceBacklog(self):
        # force it to run the next time it looks
        result = settings.backlogSearchScheduler.forceRun()
        if result:
            logger.info("Backlog search forced")
            ui.notifications.message(_('Backlog search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):

        # force it to run the next time it looks
        result = settings.dailySearchScheduler.forceRun()
        if result:
            logger.info("Daily search forced")
            ui.notifications.message(_('Daily search started'))

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        result = settings.properFinderScheduler.forceRun()
        if result:
            logger.info("Find propers search forced")
            ui.notifications.message(_('Find propers search started'))

        return self.redirect("/manage/manageSearches/")

    def forceSubtitlesFinder(self):
        # force it to run the next time it looks
        result = settings.subtitlesFinderScheduler.forceRun()
        if result:
            logger.info("Subtitle search forced")
            ui.notifications.message(_('Subtitle search started'))

        return self.redirect("/manage/manageSearches/")

    def forceAutoPostProcess(self):
        # force it to run the next time it looks
        result = settings.autoPostProcessorScheduler.forceRun()
        if result:
            logger.info("Auto Post Processor forced")
            ui.notifications.message(_('Auto Post Processor started'))

        return self.redirect("/manage/manageSearches/")

    def pauseBacklog(self, paused=None):
        if paused == "1":
            settings.searchQueueScheduler.action.pause_backlog()
        else:
            settings.searchQueueScheduler.action.unpause_backlog()

        return self.redirect("/manage/manageSearches/")
