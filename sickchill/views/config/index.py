import os

from tornado.web import addslash

from sickchill import settings
from sickchill.sickbeard.versionChecker import CheckVersion
from sickchill.views.common import PageTemplate
from sickchill.views.index import WebRoot
from sickchill.views.routes import Route


@Route('/config(/?.*)', name='config:main')
class Config(WebRoot):
    def __init__(self, *args, **kwargs):
        super(Config, self).__init__(*args, **kwargs)

    @staticmethod
    def ConfigMenu():
        menu = [
            {'title': _('General'), 'path': 'config/general/', 'icon': 'fa fa-cog'},
            {'title': _('Backup/Restore'), 'path': 'config/backuprestore/', 'icon': 'fa fa-floppy-o'},
            {'title': _('Search Settings'), 'path': 'config/search/', 'icon': 'fa fa-search'},
            {'title': _('Search Providers'), 'path': 'config/providers/', 'icon': 'fa fa-plug'},
            {'title': _('Subtitles Settings'), 'path': 'config/subtitles/', 'icon': 'fa fa-language'},
            {'title': _('Post Processing'), 'path': 'config/postProcessing/', 'icon': 'fa fa-refresh'},
            {'title': _('Notifications'), 'path': 'config/notifications/', 'icon': 'fa fa-bell-o'},
            {'title': _('Anime'), 'path': 'config/anime/', 'icon': 'fa fa-eye'},
        ]

        return menu

    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config.mako")

        try:
            # noinspection PyUnresolvedReferences
            import pwd
            sr_user = pwd.getpwuid(os.getuid()).pw_name
        except ImportError:
            try:
                import getpass
                sr_user = getpass.getuser()
            except Exception:
                sr_user = 'Unknown'

        try:
            import locale
            sr_locale = locale.getdefaultlocale()
        except Exception:
            sr_locale = 'Unknown', 'Unknown'

        try:
            import ssl
            ssl_version = ssl.OPENSSL_VERSION
        except Exception:
            ssl_version = 'Unknown'

        sr_version = ''
        if settings.VERSION_NOTIFY:
            updater = CheckVersion().updater
            if updater:
                updater.need_update()
                sr_version = updater.get_cur_version()

        return t.render(
            submenu=self.ConfigMenu(), title=_('SickChill Configuration'),
            header=_('SickChill Configuration'), topmenu="config",
            sr_user=sr_user, sr_locale=sr_locale, ssl_version=ssl_version,
            sr_version=sr_version
        )
