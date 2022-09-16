import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import setup_github, try_int
from sickchill.init_helpers import setup_gettext
from sickchill.oldbeard import config, filters, helpers, ui
from sickchill.oldbeard.common import Quality, WANTED
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from .index import Config


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

    @staticmethod
    def saveRootDirs(rootDirString=None):
        settings.ROOT_DIRS = rootDirString

    @staticmethod
    def saveAddShowDefaults(
        defaultStatus, anyQualities, bestQualities, defaultSeasonFolders, subtitles=False, anime=False, scene=False, defaultStatusAfter=WANTED
    ):

        if anyQualities:
            anyQualities = anyQualities.split(",")
        else:
            anyQualities = []

        if bestQualities:
            bestQualities = bestQualities.split(",")
        else:
            bestQualities = []

        newQuality = Quality.combineQualities([int(quality) for quality in anyQualities], [int(quality) for quality in bestQualities])

        settings.STATUS_DEFAULT = int(defaultStatus)
        settings.STATUS_DEFAULT_AFTER = int(defaultStatusAfter)
        settings.QUALITY_DEFAULT = int(newQuality)

        settings.SEASON_FOLDERS_DEFAULT = config.checkbox_to_value(defaultSeasonFolders)
        settings.SUBTITLES_DEFAULT = config.checkbox_to_value(subtitles)

        settings.ANIME_DEFAULT = config.checkbox_to_value(anime)

        settings.SCENE_DEFAULT = config.checkbox_to_value(scene)
        sickchill.start.save_config()

        ui.notifications.message(_("Saved Defaults"), _('Your "add show" defaults have been set to your current selections.'))

    def saveGeneral(
        self,
        log_nr=5,
        log_size=1,
        web_port=None,
        notify_on_login=None,
        web_log=None,
        encryption_version=None,
        web_ipv6=None,
        trash_remove_show=None,
        trash_rotate_logs=None,
        update_frequency=None,
        skip_removed_files=None,
        indexerDefaultLang="en",
        ep_default_deleted_status=None,
        launch_browser=None,
        no_lgmargin=None,
        showupdate_hour=3,
        web_username=None,
        api_key=None,
        indexer_default=None,
        timezone_display=None,
        cpu_preset="NORMAL",
        web_password=None,
        version_notify=None,
        enable_https=None,
        https_cert=None,
        https_key=None,
        handle_reverse_proxy=None,
        sort_article=None,
        grammar_articles=None,
        auto_update=None,
        notify_on_update=None,
        proxy_setting=None,
        proxy_indexers=None,
        anon_redirect=None,
        calendar_unprotected=None,
        calendar_icons=None,
        debug=None,
        ssl_verify=None,
        no_restart=None,
        coming_eps_missed_range=None,
        fuzzy_dating=None,
        trim_zero=None,
        date_preset=None,
        date_preset_na=None,
        time_preset=None,
        indexer_timeout=None,
        download_url=None,
        rootDir=None,
        theme_name=None,
        default_page=None,
        fanart_background=None,
        fanart_background_opacity=None,
        sickchill_background=None,
        sickchill_background_path=None,
        custom_css=None,
        custom_css_path=None,
        git_username=None,
        git_token=None,
        display_all_seasons=None,
        gui_language=None,
        ignore_broken_symlinks=None,
        ended_shows_update_interval=None,
        log_dir=None,
    ):

        results = []

        if gui_language != settings.GUI_LANG:
            setup_gettext(gui_language)
            settings.GUI_LANG = gui_language

        # Misc
        settings.DOWNLOAD_URL = download_url
        settings.INDEXER_DEFAULT_LANGUAGE = indexerDefaultLang
        settings.EP_DEFAULT_DELETED_STATUS = ep_default_deleted_status
        settings.SKIP_REMOVED_FILES = config.checkbox_to_value(skip_removed_files)
        settings.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        settings.NO_LGMARGIN = config.checkbox_to_value(no_lgmargin)
        config.change_showupdate_hour(showupdate_hour)
        config.change_version_notify(version_notify)
        settings.AUTO_UPDATE = config.checkbox_to_value(auto_update)
        settings.NOTIFY_ON_UPDATE = config.checkbox_to_value(notify_on_update)
        settings.LOG_NR = log_nr
        settings.LOG_SIZE = float(log_size)
        if not config.change_log_dir(log_dir):
            results += [_("Unable to create directory {log_dir} or it is not writable, log directory not changed.").format(log_dir=os.path.normpath(log_dir))]
        settings.WEB_LOG = config.checkbox_to_value(web_log)

        settings.TRASH_REMOVE_SHOW = config.checkbox_to_value(trash_remove_show)
        settings.TRASH_ROTATE_LOGS = config.checkbox_to_value(trash_rotate_logs)
        settings.IGNORE_BROKEN_SYMLINKS = config.checkbox_to_value(ignore_broken_symlinks)
        config.change_update_frequency(update_frequency)
        settings.LAUNCH_BROWSER = config.checkbox_to_value(launch_browser)
        settings.SORT_ARTICLE = config.checkbox_to_value(sort_article)
        settings.GRAMMAR_ARTICLES = grammar_articles
        settings.CPU_PRESET = cpu_preset
        settings.ANON_REDIRECT = anon_redirect
        settings.PROXY_SETTING = proxy_setting
        if settings.PROXY_SETTING:
            settings.PROXY_SETTING = config.clean_url(settings.PROXY_SETTING).rstrip("/")
        settings.PROXY_INDEXERS = config.checkbox_to_value(proxy_indexers)

        settings.GIT_USERNAME = git_username

        tmp_git_token = filters.unhide(settings.GIT_TOKEN, git_token)
        if settings.GIT_TOKEN != tmp_git_token:
            # Re-Initializes oldbeard.gh, so a restart isn't necessary
            settings.GIT_TOKEN = tmp_git_token
            setup_github()

        settings.CALENDAR_UNPROTECTED = config.checkbox_to_value(calendar_unprotected)
        settings.CALENDAR_ICONS = config.checkbox_to_value(calendar_icons)
        settings.NO_RESTART = config.checkbox_to_value(no_restart)
        settings.DEBUG = config.checkbox_to_value(debug)
        logger.set_level()

        settings.SSL_VERIFY = config.checkbox_to_value(ssl_verify)
        helpers.set_opener(settings.SSL_VERIFY)

        settings.COMING_EPS_MISSED_RANGE = config.min_max(coming_eps_missed_range, 7, 0, 42810)

        settings.DISPLAY_ALL_SEASONS = config.checkbox_to_value(display_all_seasons)
        settings.NOTIFY_ON_LOGIN = config.checkbox_to_value(notify_on_login)
        settings.WEB_PORT = try_int(web_port)
        settings.WEB_IPV6 = config.checkbox_to_value(web_ipv6)
        settings.ENCRYPTION_VERSION = config.checkbox_to_value(encryption_version, value_on=2, value_off=0)
        settings.WEB_USERNAME = web_username
        settings.WEB_PASSWORD = filters.unhide(settings.WEB_PASSWORD, web_password)

        settings.FUZZY_DATING = config.checkbox_to_value(fuzzy_dating)
        settings.TRIM_ZERO = config.checkbox_to_value(trim_zero)

        if date_preset:
            settings.DATE_PRESET = date_preset

        if indexer_default:
            settings.INDEXER_DEFAULT = try_int(indexer_default)

        if indexer_timeout:
            settings.INDEXER_TIMEOUT = try_int(indexer_timeout)

        if time_preset:
            settings.TIME_PRESET_W_SECONDS = time_preset
            settings.TIME_PRESET = time_preset.replace(":%S", "")

        settings.TIMEZONE_DISPLAY = timezone_display

        settings.API_KEY = api_key

        settings.ENABLE_HTTPS = config.checkbox_to_value(enable_https)

        if not config.change_https_cert(https_cert):
            results += [_("Unable to create directory {directory}, https cert directory not changed.").format(directory=os.path.normpath(https_cert))]

        if not config.change_https_key(https_key):
            results += [_("Unable to create directory {directory}, https key directory not changed.").format(directory=os.path.normpath(https_key))]

        settings.HANDLE_REVERSE_PROXY = config.checkbox_to_value(handle_reverse_proxy)

        settings.THEME_NAME = theme_name
        settings.SICKCHILL_BACKGROUND = config.checkbox_to_value(sickchill_background)
        config.change_sickchill_background(sickchill_background_path)
        settings.FANART_BACKGROUND = config.checkbox_to_value(fanart_background)
        settings.FANART_BACKGROUND_OPACITY = fanart_background_opacity
        settings.CUSTOM_CSS = config.checkbox_to_value(custom_css)
        config.change_custom_css(custom_css_path)

        settings.ENDED_SHOWS_UPDATE_INTERVAL = int(ended_shows_update_interval)

        settings.DEFAULT_PAGE = default_page

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/general/")
