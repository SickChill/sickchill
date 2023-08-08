from sickchill import logger, settings
from sickchill.oldbeard import ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Manage


@Route("/manage/manageSearches(/?.*)", name="manage:searches")
class ManageSearches(Manage):
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="manage_manageSearches.mako")

        # TODO: Add fancy ajax table that shows progress of each thread in the UI
        # t.backlog_search_pi = settings.backlogSearchScheduler.action.getProgressIndicator()
        # t.daily_search_pi = settings.dailySearchScheduler.action.getProgressIndicator()
        # t.proper_finder_pi = settings.properFinderScheduler.action.getProgressIndicator()
        # t.search_queue_pi = settings.searchQueueScheduler.action.getProgressIndicator()
        # t.show_queue_pi = settings.showQueueScheduler.action.getProgressIndicator()
        # t.show_updates_pi = settings.showUpdateScheduler.action.getProgressIndicator()
        # t.subtitles_pi = settings.subtitlesFinderScheduler.action.getProgressIndicator()
        # t.post_processor_pi = settings.postProcessorTaskScheduler.action.getProgressIndicator()
        # t.notifications_pi = settings.notificationsTaskScheduler.action.getProgressIndicator()
        # t.auto_post_process_pi = settings.autoPostProcessorScheduler.action.getProgressIndicator()
        # t.version_pi = settings.versionCheckScheduler.action.getProgressIndicator()
        # t.trakt_checker_pi = settings.traktCheckerScheduler.action.getProgressIndicator()

        return t.render(
            backlogPaused=settings.searchQueueScheduler.action.is_backlog_paused(),
            backlogRunning=settings.searchQueueScheduler.action.is_backlog_in_progress(),
            dailySearchStatus=settings.dailySearchScheduler.action.amActive,
            findPropersStatus=settings.properFinderScheduler.action.amActive,
            subtitlesFinderStatus=settings.subtitlesFinderScheduler.action.amActive,
            autoPostProcessorStatus=settings.autoPostProcessorScheduler.action.amActive,
            queueLength=settings.searchQueueScheduler.action.queue_length(),
            processing_queue=settings.postProcessorTaskScheduler.action.queue_length(),
            title=_("Manage Searches"),
            header=_("Manage Searches"),
            topmenu="manage",
            controller="manage",
            action="manageSearches",
        )

    def forceBacklog(self):
        # force it to run the next time it looks
        result = settings.backlogSearchScheduler.forceRun()
        if result:
            logger.info("Backlog search forced")
            ui.notifications.message(_("Backlog search started"))

        return self.redirect("/manage/manageSearches/")

    def forceSearch(self):
        # force it to run the next time it looks
        result = settings.dailySearchScheduler.forceRun()
        if result:
            logger.info("Daily search forced")
            ui.notifications.message(_("Daily search started"))

        return self.redirect("/manage/manageSearches/")

    def forceFindPropers(self):
        # force it to run the next time it looks
        result = settings.properFinderScheduler.forceRun()
        if result:
            logger.info("Find propers search forced")
            ui.notifications.message(_("Find propers search started"))

        return self.redirect("/manage/manageSearches/")

    def forceSubtitlesFinder(self):
        # force it to run the next time it looks
        result = settings.subtitlesFinderScheduler.forceRun()
        if result:
            logger.info("Subtitle search forced")
            ui.notifications.message(_("Subtitle search started"))

        return self.redirect("/manage/manageSearches/")

    def forceAutoPostProcess(self):
        # force it to run the next time it looks
        result = settings.autoPostProcessorScheduler.forceRun()
        if result:
            logger.info("Auto Post Processor forced")
            ui.notifications.message(_("Auto Post Processor started"))

        return self.redirect("/manage/manageSearches/")

    def pauseBacklog(self, paused=None):
        if paused == "1":
            settings.searchQueueScheduler.action.pause_backlog()
        else:
            settings.searchQueueScheduler.action.unpause_backlog()

        return self.redirect("/manage/manageSearches/")
