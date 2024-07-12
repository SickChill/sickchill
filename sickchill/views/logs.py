from tornado.web import addslash

import sickchill.oldbeard
from sickchill import logger
from sickchill.helper import try_int
from sickchill.oldbeard import classes
from sickchill.views.common import PageTemplate
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route("/errorlogs(/?.*)", name="logs:error")
class ErrorLogs(WebRoot):
    def __ErrorLogsMenu(self, level):
        menu = [
            {
                "title": _("Clear Errors"),
                "path": "errorlogs/clearerrors/",
                "requires": self.haveErrors() and level == logger.ERROR,
                "icon": "ui-icon ui-icon-trash",
            },
            {
                "title": _("Clear Warnings"),
                "path": f"errorlogs/clearerrors/?level={logger.WARNING}",
                "requires": self.haveWarnings() and level == logger.WARNING,
                "icon": "ui-icon ui-icon-trash",
            },
        ]

        return menu

    @addslash
    def index(self):
        level = try_int(self.get_query_argument("level", str(logger.ERROR)), logger.ERROR)

        t = PageTemplate(rh=self, filename="errorlogs.mako")
        return t.render(
            header=_("Logs &amp; Errors"),
            title=_("Logs &amp; Errors"),
            topmenu="system",
            submenu=self.__ErrorLogsMenu(level),
            logLevel=level,
            controller="errorlogs",
            action="index",
        )

    @staticmethod
    def haveErrors():
        return len(classes.ErrorViewer.errors) > 0

    @staticmethod
    def haveWarnings():
        return len(classes.WarningViewer.errors) > 0

    def clearerrors(self):
        level = try_int(self.get_query_argument("level", str(logger.ERROR)), logger.ERROR)
        if int(level) == logger.WARNING:
            classes.WarningViewer.clear()
        else:
            classes.ErrorViewer.clear()

        return self.redirect("/errorlogs/viewlog/")

    def viewlog(self):
        min_level = try_int(self.get_body_argument("min_level", str(logger.INFO)), logger.INFO)
        log_filter = self.get_body_argument("log_filter", "<NONE>")
        log_search = self.get_body_argument("log_search", "")
        max_lines = try_int(self.get_body_argument("max_lines", str(500)), 500)
        data = sickchill.logger.log_data(min_level, log_filter, log_search, max_lines)

        t = PageTemplate(rh=self, filename="viewlogs.mako")
        return t.render(
            header=_("Log File"),
            title=_("Logs"),
            topmenu="system",
            log_data="".join(data),
            min_level=min_level,
            log_filter=log_filter,
            log_search=log_search,
            controller="errorlogs",
            action="viewlogs",
        )
