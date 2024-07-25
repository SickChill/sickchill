import os
import time

from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup
from mako.runtime import UNDEFINED
from mako.template import Template
from tornado.escape import linkify

from sickchill import logger, settings
from sickchill.logging.weblog import WebErrorViewer
from sickchill.oldbeard import helpers

mako_lookup = {}


def get_lookup():
    return mako_lookup.setdefault(
        "mako",
        TemplateLookup(
            directories=[os.path.join(settings.PROG_DIR, "gui/" + settings.GUI_NAME + "/views/")],
            module_directory=os.path.join(settings.CACHE_DIR, "mako"),
            strict_undefined=settings.DEVELOPER or settings.DEBUG,
            format_exceptions=True,
            imports=["from sickchill.oldbeard.filters import checked, disabled, hidden, selected"],
        ),
    )


class PageTemplate(Template):
    def __init__(self, rh, filename, test_exception: bool = False):
        super().__init__(filename)
        self.test_exception = test_exception
        self.context = {}

        lookup = get_lookup()
        self.template = lookup.get_template(filename)

        self.context["scRoot"] = settings.WEB_ROOT
        self.context["sc_default_page"] = settings.DEFAULT_PAGE
        self.context["current_user"] = rh.get_current_user()
        self.context["page_load_start_time"] = rh.page_load_start_time
        self.context["static_url"] = rh.static_url
        self.context["reverse_url"] = rh.reverse_url
        self.context["linkify"] = linkify

        self.context["error_count"] = WebErrorViewer.num_errors()
        self.context["warning_count"] = WebErrorViewer.num_warnings()
        self.context["process_id"] = str(settings.PID)

        self.context["title"] = "FixME"
        self.context["header"] = "FixME"
        self.context["topmenu"] = "FixME"
        self.context["submenu"] = []
        self.context["controller"] = "FixME"
        self.context["action"] = "FixME"
        self.context["show"] = UNDEFINED
        self.context["manage_torrents_url"] = helpers.manage_torrents_url()
        self.context["get_current_user"] = rh.get_current_user
        self.context["remote_ip"] = rh.request.remote_ip

    def render(self, *args, **kwargs):
        self.context["mako_load_start_time"] = time.time()
        context = self.context
        context.update(kwargs)
        # noinspection PyBroadException
        try:
            if self.test_exception:
                raise Exception("This is a test Exception")
            return self.template.render_unicode(*args, **context)
        except Exception as error:
            logger.info(f"A mako render error occurred: {error}")
            context["title"] = "500"
            context["header"] = _("Mako Error")
            context["backtrace"] = RichTraceback(error=error)
            lookup = TemplateLookup(
                directories=[os.path.join(settings.PROG_DIR, "gui/" + settings.GUI_NAME + "/views/")],
                strict_undefined=settings.DEVELOPER or settings.DEBUG,
                format_exceptions=True,
            )
            return lookup.get_template("500.mako").render_unicode(*args, **context)
