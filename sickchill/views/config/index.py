import os

from tornado.web import addslash

from sickchill.init_helpers import get_current_version
from sickchill.views.common import PageTemplate
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route("/config(/?.*)", name="config:main")
class Config(WebRoot):
    @staticmethod
    def ConfigMenu():
        menu = [
            {"title": _("General"), "path": "config/general/", "icon": "fa fa-cog"},
            {"title": _("Backup/Restore"), "path": "config/backuprestore/", "icon": "fa fa-floppy-o"},
            {"title": _("Search Settings"), "path": "config/search/", "icon": "fa fa-search"},
            {"title": _("Search Providers"), "path": "config/providers/", "icon": "fa fa-plug"},
            {"title": _("Subtitles Settings"), "path": "config/subtitles/", "icon": "fa fa-language"},
            {"title": _("Post Processing"), "path": "config/postProcessing/", "icon": "fa fa-refresh"},
            {"title": _("Notifications"), "path": "config/notifications/", "icon": "fa fa-bell-o"},
            {"title": _("Anime"), "path": "config/anime/", "icon": "fa fa-eye"},
        ]

        return menu

    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config.mako")
        try:
            import getpass

            sc_user = getpass.getuser()
        except Exception:
            sc_user = os.getuid()

        try:
            import locale

            sc_locale = locale.getdefaultlocale()
        except Exception:
            sc_locale = "Unknown", "Unknown"

        try:
            import ssl

            ssl_version = ssl.OPENSSL_VERSION
        except Exception:
            ssl_version = "Unknown"

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("SickChill Configuration"),
            header=_("SickChill Configuration"),
            topmenu="config",
            sc_user=sc_user,
            sc_locale=sc_locale,
            ssl_version=ssl_version,
            sc_version=get_current_version(),
        )
