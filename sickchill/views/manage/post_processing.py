from tornado.web import addslash

import sickchill.start
from sickchill import settings
from sickchill.oldbeard import config
from sickchill.views.common import PageTemplate
from sickchill.views.home import Home
from sickchill.views.routes import Route


@Route("/home/postprocess(/?.*)", name="home:postprocess")
class PostProcess(Home):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="home_postprocess.mako")
        return t.render(
            title=_("Post Processing"),
            header=_("Post Processing"),
            topmenu="home",
            controller="home",
            action="postProcess",
        )

    def processEpisode(self):
        """Queue post-processing for a download folder.

        nzbToMedia / nzbToSickBeard call this via GET with query params including
        ``quiet=1`` and expect a **plain-text** processing log (not the HTML UI).
        The browser form POSTs without ``quiet`` and receives the HTML results page.
        """
        # Prefer get_argument so both query (scripts) and body (UI form) work.
        process_path = self.get_argument("dir", default="") or self.get_argument("proc_dir", default="")
        if not process_path:
            return self.redirect("/home/postprocess/")

        release_name = self.get_argument("nzbName", default=None)
        process_method = self.get_argument("process_method", default=None)
        delete_on = self.get_argument("delete_on", default="0")
        force = config.checkbox_to_value(self.get_argument("force", default="False"))
        is_priority = config.checkbox_to_value(self.get_argument("is_priority", default="False"))
        failed = config.checkbox_to_value(self.get_argument("failed", default="False"))
        no_queue = config.checkbox_to_value(self.get_argument("no_queue", default="False"))
        quiet = config.checkbox_to_value(self.get_argument("quiet", default="0"))
        # Prefer type (scripts), then proc_type (UI); empty type must not hide a set proc_type.
        mode = self.get_argument("type", default="") or self.get_argument("proc_type", default="") or "manual"

        # Persist the seven UI fields when Process is pressed. Scripts use dir= and quiet=1.
        if not quiet and self.get_argument("proc_dir", default=""):
            settings.MANUAL_POSTPROCESS_DIR = process_path
            settings.MANUAL_POSTPROCESS_METHOD = process_method or ""
            settings.MANUAL_POSTPROCESS_FORCE = bool(force)
            settings.MANUAL_POSTPROCESS_PRIORITY = bool(is_priority)
            settings.MANUAL_POSTPROCESS_DELETE = config.checkbox_to_value(delete_on)
            settings.MANUAL_POSTPROCESS_NO_QUEUE = bool(no_queue)
            settings.MANUAL_POSTPROCESS_FAILED = bool(failed)
            sickchill.start.save_config()

        result = settings.postProcessorTaskScheduler.action.add_item(
            process_path,
            release_name,
            method=process_method,
            force=force,
            is_priority=is_priority,
            delete=delete_on,
            failed=failed,
            mode=mode,
            no_queue=no_queue,
        )

        # nzbToMedia parses plain-text status lines ("Successfully processed", etc.)
        if quiet:
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            return result or ""

        if result:
            result = result.replace("\n", "<br>\n")

        return self._genericMessage("Postprocessing results", result)
