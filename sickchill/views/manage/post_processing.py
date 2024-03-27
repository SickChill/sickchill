from tornado.web import addslash

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
        # Manual mode post processing
        mode = "manual"
        release_name = self.get_body_argument("nzbName", default=None)
        process_method = self.get_body_argument("process_method", default=None)
        delete_on = self.get_body_argument("delete_on", default="0")
        force = config.checkbox_to_value(self.get_body_argument("force", default="False"))
        is_priority = config.checkbox_to_value(self.get_body_argument("is_priority", default="False"))
        failed = config.checkbox_to_value(self.get_body_argument("failed", default="False"))
        force_next = config.checkbox_to_value(self.get_body_argument("force_next", default="False"))

        process_path = self.get_body_argument("dir", self.get_body_argument("proc_dir", default=""))
        if not process_path:
            return self.redirect("/home/postprocess/")

        result = settings.postProcessorTaskScheduler.action.add_item(
            process_path,
            release_name,
            method=process_method,
            force=force,
            is_priority=is_priority,
            delete=delete_on,
            failed=failed,
            mode=mode,
            force_next=force_next,
        )

        if result:
            result = result.replace("\n", "<br>\n")

        return self._genericMessage("Postprocessing results", result)
