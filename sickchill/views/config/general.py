import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.init_helpers import setup_gettext
from sickchill.oldbeard import config, filters, helpers, ui
from sickchill.oldbeard.common import Quality
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/general(/?.*)", name="config:general")
class ConfigGeneral(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_general.mako")

        return t.render(
            title=_("Config - General"), header=_("General Configuration"), topmenu="config", submenu=self.ConfigMenu(), controller="config", action="index"
        )

    @staticmethod
    def generateApiKey():
        return helpers.generateApiKey()

    def saveRootDirs(self):
        settings.ROOT_DIRS = self.get_body_argument("rootDirString")

    def saveAddShowDefaults(self):
        any_qualities = [int(quality) for quality in self.get_body_arguments("anyQualities[]")]
        best_qualities = [int(quality) for quality in self.get_body_arguments("bestQualities[]")]

        settings.QUALITY_DEFAULT = Quality.combineQualities(any_qualities, best_qualities)

        settings.STATUS_DEFAULT = int(self.get_body_argument("defaultStatus", settings.STATUS_DEFAULT_AFTER))
        settings.STATUS_DEFAULT_AFTER = int(self.get_body_argument("defaultStatusAfter", settings.STATUS_DEFAULT_AFTER))

        settings.WHITELIST_DEFAULT = self.get_body_arguments("whitelist[]")
        settings.BLACKLIST_DEFAULT = self.get_body_arguments("blacklist[]")

        settings.SEASON_FOLDERS_DEFAULT = config.checkbox_to_value(self.get_body_argument("defaultSeasonFolders", settings.SEASON_FOLDERS_DEFAULT))
        settings.SUBTITLES_DEFAULT = config.checkbox_to_value(self.get_body_argument("subtitles", settings.SUBTITLES_DEFAULT))
        settings.ANIME_DEFAULT = config.checkbox_to_value(self.get_body_argument("anime", settings.ANIME_DEFAULT))
        settings.SCENE_DEFAULT = config.checkbox_to_value(self.get_body_argument("scene", settings.SCENE_DEFAULT))

        sickchill.start.save_config()

        ui.notifications.message(_("Saved Defaults"), _('Your "add show" defaults have been set to your current selections.'))

    def saveGeneral(self):
        gui_language = self.get_body_argument("gui_language", default=None)
        encryption_version = self.get_body_argument("encryption_version", default=None)
        indexer_default = self.get_body_argument("indexer_default", default=None)
        web_password = self.get_body_argument("web_password", default=None)
        https_cert = self.get_body_argument("https_cert", default=None)
        https_key = self.get_body_argument("https_key", default=None)
        coming_eps_missed_range = self.get_body_argument("coming_eps_missed_range", default=None)
        date_preset = self.get_body_argument("date_preset", default=None)
        time_preset = self.get_body_argument("time_preset", default=None)
        indexer_timeout = self.get_body_argument("indexer_timeout", default=None)
        log_dir = self.get_body_argument("log_dir", default="")

        results = []

        if gui_language != settings.GUI_LANG:
            setup_gettext(gui_language)
            settings.GUI_LANG = gui_language

        # Misc
        settings.DOWNLOAD_URL = self.get_body_argument("download_url", default=None)
        settings.INDEXER_DEFAULT_LANGUAGE = self.get_body_argument("indexerDefaultLang", default="en")
        settings.EP_DEFAULT_DELETED_STATUS = self.get_body_argument("ep_default_deleted_status", default=None)
        settings.SKIP_REMOVED_FILES = config.checkbox_to_value(self.get_body_argument("skip_removed_files", default=None))
        settings.LAUNCH_BROWSER = config.checkbox_to_value(self.get_body_argument("launch_browser", default=None))
        settings.NO_LGMARGIN = config.checkbox_to_value(self.get_body_argument("no_lgmargin", default=None))
        config.change_showupdate_hour(self.get_body_argument("showupdate_hour", default="3"))
        config.change_version_notify(self.get_body_argument("version_notify", default=None))
        settings.AUTO_UPDATE = config.checkbox_to_value(self.get_body_argument("auto_update", default=None))
        settings.NOTIFY_ON_UPDATE = config.checkbox_to_value(self.get_body_argument("notify_on_update", default=None))
        settings.LOG_NR = int(self.get_body_argument("log_nr", default="5"))
        settings.LOG_SIZE = float(self.get_body_argument("log_size", default="1"))
        if not config.change_log_dir(log_dir):
            results += [_("Unable to create directory {log_dir} or it is not writable, log directory not changed.").format(log_dir=os.path.normpath(log_dir))]
        settings.WEB_LOG = config.checkbox_to_value(self.get_body_argument("web_log", default=None))

        settings.TRASH_REMOVE_SHOW = config.checkbox_to_value(self.get_body_argument("trash_remove_show", default=None))
        settings.TRASH_ROTATE_LOGS = config.checkbox_to_value(self.get_body_argument("trash_rotate_logs", default=None))
        settings.IGNORE_BROKEN_SYMLINKS = config.checkbox_to_value(self.get_body_argument("ignore_broken_symlinks", default=None))
        config.change_update_frequency(self.get_body_argument("update_frequency", default=None))
        settings.SORT_ARTICLE = config.checkbox_to_value(self.get_body_argument("sort_article", default=None))
        settings.GRAMMAR_ARTICLES = self.get_body_argument("grammar_articles", default=None)
        settings.CPU_PRESET = self.get_body_argument("cpu_preset", default="NORMAL")
        settings.ANON_REDIRECT = self.get_body_argument("anon_redirect", default=None)
        settings.PROXY_SETTING = self.get_body_argument("proxy_setting", default=None)
        if settings.PROXY_SETTING:
            settings.PROXY_SETTING = config.clean_url(settings.PROXY_SETTING).rstrip("/")
        settings.PROXY_INDEXERS = config.checkbox_to_value(self.get_body_argument("proxy_indexers", default=None))

        settings.CALENDAR_UNPROTECTED = config.checkbox_to_value(self.get_body_argument("calendar_unprotected", default=None))
        settings.CALENDAR_ICONS = config.checkbox_to_value(self.get_body_argument("calendar_icons", default=None))
        settings.NO_RESTART = config.checkbox_to_value(self.get_body_argument("no_restart", default=None))
        settings.DEBUG = config.checkbox_to_value(self.get_body_argument("debug", default=None))
        settings.DBDEBUG = config.checkbox_to_value(self.get_body_argument("dbdebug", default=None))
        logger.restart()

        settings.NOTIFY_ON_LOGGED_ERROR = config.checkbox_to_value(self.get_body_argument("notify_on_logged_error", default=None))

        settings.SSL_VERIFY = config.checkbox_to_value(self.get_body_argument("ssl_verify", default=None))
        helpers.set_opener(settings.SSL_VERIFY)

        settings.COMING_EPS_MISSED_RANGE = config.min_max(coming_eps_missed_range, 7, 0, 42810)

        settings.DISPLAY_ALL_SEASONS = config.checkbox_to_value(self.get_body_argument("display_all_seasons", default=None))
        settings.NOTIFY_ON_LOGIN = config.checkbox_to_value(self.get_body_argument("notify_on_login", default=None))
        settings.WEB_PORT = try_int(self.get_body_argument("web_port", default=None))
        settings.WEB_IPV6 = config.checkbox_to_value(self.get_body_argument("web_ipv6", default=None))
        settings.ENCRYPTION_VERSION = config.checkbox_to_value(encryption_version, value_on=2, value_off=0)
        settings.WEB_USERNAME = self.get_body_argument("web_username", default=None)
        settings.WEB_PASSWORD = filters.unhide(settings.WEB_PASSWORD, web_password)

        settings.FUZZY_DATING = config.checkbox_to_value(self.get_body_argument("fuzzy_dating", default=None))
        settings.TRIM_ZERO = config.checkbox_to_value(self.get_body_argument("trim_zero", default=None))

        if date_preset:
            settings.DATE_PRESET = self.get_body_argument("date_preset", default=None)

        if indexer_default:
            settings.INDEXER_DEFAULT = try_int(self.get_body_argument("indexer_default", default=None))

        if indexer_timeout:
            settings.INDEXER_TIMEOUT = try_int(self.get_body_argument("indexer_timeout", default=None))

        if time_preset:
            settings.TIME_PRESET_W_SECONDS = time_preset
            settings.TIME_PRESET = time_preset.replace(":%S", "")

        settings.TIMEZONE_DISPLAY = self.get_body_argument("timezone_display", default=None)

        settings.API_KEY = self.get_body_argument("api_key", default=None)

        settings.ENABLE_HTTPS = config.checkbox_to_value(self.get_body_argument("enable_https", default=None))

        if not config.change_https_cert(https_cert):
            results += [_("Unable to create directory {directory}, https cert directory not changed.").format(directory=os.path.normpath(https_cert))]

        if not config.change_https_key(https_key):
            results += [_("Unable to create directory {directory}, https key directory not changed.").format(directory=os.path.normpath(https_key))]

        settings.HANDLE_REVERSE_PROXY = config.checkbox_to_value(self.get_body_argument("handle_reverse_proxy", default=None))

        settings.THEME_NAME = self.get_body_argument("theme_name", default=None)
        settings.SICKCHILL_BACKGROUND = config.checkbox_to_value(self.get_body_argument("sickchill_background", default=None))
        config.change_sickchill_background(self.get_body_argument("sickchill_background_path", default=None))
        settings.FANART_BACKGROUND = config.checkbox_to_value(self.get_body_argument("fanart_background", default=None))
        settings.FANART_BACKGROUND_OPACITY = self.get_body_argument("fanart_background_opacity", default=None)
        settings.CUSTOM_CSS = config.checkbox_to_value(self.get_body_argument("custom_css", default=None))
        config.change_custom_css(self.get_body_argument("custom_css_path", default=None))

        settings.ENDED_SHOWS_UPDATE_INTERVAL = int(self.get_body_argument("ended_shows_update_interval", default=None))

        settings.DEFAULT_PAGE = self.get_body_argument("default_page", default=None)

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/general/")
