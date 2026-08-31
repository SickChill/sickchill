from urllib.parse import urlparse

from sickchill import logger, settings
from sickchill.oldbeard import ui
from sickchill.views.common import PageTemplate
from sickchill.views.manage.index import Manage
from sickchill.views.routes import Route


@Route("/manage/manageSearches(/?.*)", name="manage:searches")
class ManageSearches(Manage):
    def index(self):
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
            showUpdaterStatus=settings.showUpdateScheduler.action.amActive,
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
        if not settings.PROCESS_AUTOMATICALLY:
            ui.notifications.error(_("Error"), _("Auto Post Processor is disabled"))
        else:
            result = settings.autoPostProcessorScheduler.forceRun()
            if result:
                logger.info("Auto Post Processor forced")
                ui.notifications.message(_("Auto Post Processor started"))
            else:
                ui.notifications.error(_("Error"), _("Auto Post Processor is already running"))

        # Prefer staying on the page that triggered the action (navbar / Manage Searches)
        next_url = self.get_query_argument("next", default=None)
        if next_url and next_url.startswith("/") and not next_url.startswith("//"):
            return self.redirect(next_url)

        referer = self.request.headers.get("Referer") or ""
        parsed = urlparse(referer)
        if parsed.netloc == self.request.host and parsed.path.startswith("/"):
            path = parsed.path + (("?" + parsed.query) if parsed.query else "")
            return self.redirect(path)

        return self.redirect("/" + settings.DEFAULT_PAGE + "/")

    def forceShowUpdater(self):
        """Force ShowUpdater (developer mode only)."""
        if not settings.DEVELOPER:
            ui.notifications.error(_("Error"), _("Force Show Updater is only available when developer mode is enabled"))
            return self.redirect("/manage/manageSearches/")

        result = settings.showUpdateScheduler.forceRun()
        if result:
            logger.info("Show updater forced")
            ui.notifications.message(_("Show updater started"))
        else:
            ui.notifications.error(_("Error"), _("Show updater is already running"))

        return self.redirect("/manage/manageSearches/")

    def pauseBacklog(self):
        paused = self.get_query_argument("paused", default="0")
        if paused == "1":
            settings.searchQueueScheduler.action.pause_backlog()
        else:
            settings.searchQueueScheduler.action.unpause_backlog()

        return self.redirect("/manage/manageSearches/")
