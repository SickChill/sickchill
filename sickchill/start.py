import datetime
import os
import re
import shutil
import socket
import sys

import rarfile
from configobj import ConfigObj
from tornado.locale import load_gettext_translations

import sickchill
from sickchill import logger, settings, show_updater, update_manager
from sickchill.oldbeard.common import ARCHIVED, IGNORED, MULTI_EP_STRINGS, SD, SKIPPED, WANTED
from sickchill.oldbeard.config import check_section, check_setting_bool, check_setting_float, check_setting_int, check_setting_str, ConfigMigrator
from sickchill.oldbeard.databases import failed, main
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider

from .helper import setup_github
from .init_helpers import locale_dir, setup_gettext
from .oldbeard import (
    clients,
    config,
    dailysearcher,
    db,
    helpers,
    image_cache,
    naming,
    notifications_queue,
    post_processing_queue,
    properFinder,
    providers,
    scheduler,
    search_queue,
    searchBacklog,
    show_queue,
    subtitles,
    traktChecker,
)
from .oldbeard.databases import cache
from .providers import metadata
from .system.Shutdown import Shutdown


def initialize(consoleLogging=True):
    with settings.INIT_LOCK:

        if settings.__INITIALIZED__:
            return False

        check_section(settings.CFG, "General")
        check_section(settings.CFG, "Blackhole")
        check_section(settings.CFG, "Newzbin")
        check_section(settings.CFG, "SABnzbd")
        check_section(settings.CFG, "NZBget")
        check_section(settings.CFG, "KODI")
        check_section(settings.CFG, "PLEX")
        check_section(settings.CFG, "Emby")
        check_section(settings.CFG, "Growl")
        check_section(settings.CFG, "Prowl")
        check_section(settings.CFG, "Twitter")
        check_section(settings.CFG, "Boxcar2")
        check_section(settings.CFG, "NMJ")
        check_section(settings.CFG, "NMJv2")
        check_section(settings.CFG, "Synology")
        check_section(settings.CFG, "SynologyNotifier")
        check_section(settings.CFG, "pyTivo")
        check_section(settings.CFG, "NMA")
        check_section(settings.CFG, "Pushalot")
        check_section(settings.CFG, "Pushbullet")
        check_section(settings.CFG, "Subtitles")
        check_section(settings.CFG, "pyTivo")
        check_section(settings.CFG, "Slack")
        check_section(settings.CFG, "RocketChat")
        check_section(settings.CFG, "Discord")

        # Need to be before any passwords
        settings.ENCRYPTION_VERSION = check_setting_int(settings.CFG, "General", "encryption_version", min_val=0, max_val=2)
        settings.ENCRYPTION_SECRET = check_setting_str(settings.CFG, "General", "encryption_secret", helpers.generateCookieSecret(), censor_log=True)

        # git login info
        settings.GIT_USERNAME = check_setting_str(settings.CFG, "General", "git_username")
        settings.GIT_TOKEN = check_setting_str(settings.CFG, "General", "git_token_password", censor_log=True)  # encryption needed
        settings.DEVELOPER = check_setting_bool(settings.CFG, "General", "developer")

        # debugging
        settings.DEBUG = check_setting_bool(settings.CFG, "General", "debug")
        settings.DBDEBUG = check_setting_bool(settings.CFG, "General", "dbdebug")

        settings.DEFAULT_PAGE = check_setting_str(settings.CFG, "General", "default_page", "home")
        if settings.DEFAULT_PAGE not in ("home", "schedule", "history", "news", "IRC"):
            settings.DEFAULT_PAGE = "home"

        settings.LOG_DIR = check_setting_str(settings.CFG, "General", "log_dir", os.path.normpath(os.path.join(settings.DATA_DIR, "Logs")))
        settings.LOG_NR = check_setting_int(settings.CFG, "General", "log_nr", 5, min_val=1)  # Default to 5 backup file (sickchill.log.x)
        settings.LOG_SIZE = check_setting_float(settings.CFG, "General", "log_size", 10.0, min_val=0.5)  # Default to max 10MB per logfile

        if settings.LOG_SIZE > 100:
            settings.LOG_SIZE = 10.0
        fileLogging = True

        if not helpers.makeDir(settings.LOG_DIR) or not os.access(settings.LOG_DIR, os.W_OK):
            sys.stderr.write("!!! No log folder or log folder not writable, logging to console only!\n")
            fileLogging = False

        # init logging
        logger.init_logging(console_logging=consoleLogging, file_logging=fileLogging, debug_logging=settings.DEBUG, database_logging=settings.DBDEBUG)

        # Initializes oldbeard.gh
        setup_github()

        settings.GUI_NAME = check_setting_str(settings.CFG, "GUI", "gui_name", "slick")
        settings.GUI_LANG = check_setting_str(settings.CFG, "GUI", "language")

        setup_gettext(settings.GUI_LANG)

        load_gettext_translations(locale_dir, "messages")

        settings.CACHE_DIR = os.path.normpath(os.path.join(settings.DATA_DIR, "cache"))

        # Check if we need to perform a restore of the cache folder
        try:
            restoreDir = os.path.join(settings.DATA_DIR, "restore")
            if os.path.exists(restoreDir) and os.path.exists(os.path.join(restoreDir, "cache")):

                def restoreCache(srcDir, dstDir):
                    def path_leaf(path):
                        head, tail = os.path.split(path)
                        return tail or os.path.basename(head)

                    try:
                        if os.path.isdir(dstDir):
                            # noinspection PyTypeChecker
                            bakFilename = "{0}-{1}".format(path_leaf(dstDir), datetime.datetime.strftime(datetime.datetime.now(), "%Y%m%d_%H%M%S"))
                            shutil.move(dstDir, os.path.join(os.path.dirname(dstDir), bakFilename))

                        shutil.move(srcDir, dstDir)
                        logger.info("Restore: restoring cache successful")
                    except Exception as er:
                        logger.exception(f"Restore: restoring cache failed: {er}")

                restoreCache(os.path.join(restoreDir, "cache"), settings.CACHE_DIR)
        except Exception as error:
            logger.exception(f"Restore: restoring cache failed: {error}")
        finally:
            if os.path.exists(os.path.join(settings.DATA_DIR, "restore")):
                try:
                    shutil.rmtree(os.path.join(settings.DATA_DIR, "restore"))
                except Exception as error:
                    logger.exception(f"Restore: settings.Unable to remove the restore directory: {error}")

                for cleanupDir in ["mako", "sessions", "indexers", "rss"]:
                    try:
                        shutil.rmtree(os.path.join(settings.CACHE_DIR, cleanupDir))
                    except Exception as error:
                        if cleanupDir not in ["rss", "sessions", "indexers"]:
                            logger.info(f"Restore: Unable to remove the cache/{cleanupDir} directory: {error}")

        settings.IMAGE_CACHE = image_cache.ImageCache()
        settings.THEME_NAME = check_setting_str(settings.CFG, "GUI", "theme_name", "dark")
        settings.SICKCHILL_BACKGROUND = check_setting_bool(settings.CFG, "GUI", "sickchill_background")
        settings.SICKCHILL_BACKGROUND_PATH = check_setting_str(settings.CFG, "GUI", "sickchill_background_path")
        settings.FANART_BACKGROUND = check_setting_bool(settings.CFG, "GUI", "fanart_background", True)
        settings.FANART_BACKGROUND_OPACITY = check_setting_float(settings.CFG, "GUI", "fanart_background_opacity", 0.4, min_val=0.1, max_val=1.0)
        settings.CUSTOM_CSS = check_setting_bool(settings.CFG, "GUI", "custom_css")
        settings.CUSTOM_CSS_PATH = check_setting_str(settings.CFG, "GUI", "custom_css_path")

        settings.SOCKET_TIMEOUT = check_setting_int(settings.CFG, "General", "socket_timeout", 30, min_val=0)
        socket.setdefaulttimeout(settings.SOCKET_TIMEOUT)

        try:
            settings.WEB_PORT = check_setting_int(settings.CFG, "General", "web_port", 8081, min_val=21, max_val=65535)
        except Exception:
            settings.WEB_PORT = 8081

        settings.WEB_HOST = check_setting_str(settings.CFG, "General", "web_host", "0.0.0.0")
        settings.WEB_IPV6 = check_setting_bool(settings.CFG, "General", "web_ipv6")
        settings.WEB_ROOT = check_setting_str(settings.CFG, "General", "web_root").rstrip("/")
        settings.WEB_LOG = check_setting_bool(settings.CFG, "General", "web_log")
        settings.WEB_USERNAME = check_setting_str(settings.CFG, "General", "web_username", censor_log=True)
        settings.WEB_PASSWORD = check_setting_str(settings.CFG, "General", "web_password", censor_log=True)
        settings.WEB_COOKIE_SECRET = check_setting_str(settings.CFG, "General", "web_cookie_secret", helpers.generateCookieSecret(), censor_log=True)
        if not settings.WEB_COOKIE_SECRET:
            settings.WEB_COOKIE_SECRET = helpers.generateCookieSecret()

        settings.CF_AUTH_DOMAIN = check_setting_str(settings.CFG, "Cloudflare", "auth_domain", censor_log=True)
        settings.CF_POLICY_AUD = check_setting_str(settings.CFG, "Cloudflare", "audience_policy", censor_log=True)

        settings.WEB_USE_GZIP = check_setting_bool(settings.CFG, "General", "web_use_gzip", True)

        settings.SSL_VERIFY = check_setting_bool(settings.CFG, "General", "ssl_verify", True)
        helpers.set_opener(settings.SSL_VERIFY)

        settings.EP_DEFAULT_DELETED_STATUS = check_setting_int(settings.CFG, "General", "ep_default_deleted_status", ARCHIVED)
        if settings.EP_DEFAULT_DELETED_STATUS not in (SKIPPED, ARCHIVED, IGNORED):
            settings.EP_DEFAULT_DELETED_STATUS = ARCHIVED

        settings.LAUNCH_BROWSER = check_setting_bool(settings.CFG, "General", "launch_browser", True)

        settings.DOWNLOAD_URL = check_setting_str(settings.CFG, "General", "download_url")

        settings.LOCALHOST_IP = check_setting_str(settings.CFG, "General", "localhost_ip")

        settings.CPU_PRESET = check_setting_str(settings.CFG, "General", "cpu_preset", "NORMAL")

        settings.ANON_REDIRECT = check_setting_str(settings.CFG, "General", "anon_redirect", settings.DEFAULT_ANON_REDIRECT)
        if settings.ANON_REDIRECT == "disabled" or not settings.ANON_REDIRECT.endswith("?"):
            settings.ANON_REDIRECT = ""
        if settings.ANON_REDIRECT == "http://dereferer.org/?":
            settings.ANON_REDIRECT = settings.DEFAULT_ANON_REDIRECT

        settings.PROXY_SETTING = check_setting_str(settings.CFG, "General", "proxy_setting")
        if settings.PROXY_SETTING:
            settings.PROXY_SETTING = config.clean_url(settings.PROXY_SETTING).rstrip("/")

        settings.PROXY_INDEXERS = check_setting_bool(settings.CFG, "General", "proxy_indexers", True)

        settings.INDEXER_DEFAULT_LANGUAGE = check_setting_str(settings.CFG, "General", "indexerDefaultLang", "en")
        settings.INDEXER_DEFAULT = check_setting_int(settings.CFG, "General", "indexer_default", min_val=1, max_val=2, def_val=1)
        settings.INDEXER_TIMEOUT = check_setting_int(settings.CFG, "General", "indexer_timeout", 20, min_val=0)

        sickchill.indexer = sickchill.ShowIndexer()

        settings.TVDB_USER = check_setting_str(settings.CFG, "General", "tvdb_user")
        settings.TVDB_USER_KEY = check_setting_str(settings.CFG, "General", "tvdb_user_key", censor_log=True)

        settings.TRASH_REMOVE_SHOW = check_setting_bool(settings.CFG, "General", "trash_remove_show")
        settings.TRASH_ROTATE_LOGS = check_setting_bool(settings.CFG, "General", "trash_rotate_logs")

        settings.IGNORE_BROKEN_SYMLINKS = check_setting_bool(settings.CFG, "General", "ignore_broken_symlinks")

        settings.SORT_ARTICLE = check_setting_bool(settings.CFG, "General", "sort_article")
        settings.GRAMMAR_ARTICLES = check_setting_str(settings.CFG, "Localization", "articles", settings.GRAMMAR_ARTICLES)

        settings.API_KEY = check_setting_str(settings.CFG, "General", "api_key", censor_log=True)

        settings.ENABLE_HTTPS = check_setting_bool(settings.CFG, "General", "enable_https")

        settings.NOTIFY_ON_LOGIN = check_setting_bool(settings.CFG, "General", "notify_on_login")

        settings.HTTPS_CERT = check_setting_str(settings.CFG, "General", "https_cert", "server.crt")
        settings.HTTPS_KEY = check_setting_str(settings.CFG, "General", "https_key", "server.key")

        settings.HANDLE_REVERSE_PROXY = check_setting_bool(settings.CFG, "General", "handle_reverse_proxy")

        settings.ROOT_DIRS = check_setting_str(settings.CFG, "General", "root_dirs")
        if not re.match(r"\d+\|[^|]+(?:\|[^|]+)*", settings.ROOT_DIRS):
            settings.ROOT_DIRS = ""

        settings.QUALITY_DEFAULT = check_setting_int(settings.CFG, "General", "quality_default", SD)
        settings.QUALITY_ALLOW_HEVC = check_setting_bool(settings.CFG, "General", "quality_allow_hevc", False)
        settings.STATUS_DEFAULT = check_setting_int(settings.CFG, "General", "status_default", SKIPPED)
        if settings.STATUS_DEFAULT not in (SKIPPED, WANTED, IGNORED):
            settings.STATUS_DEFAULT = SKIPPED
        settings.STATUS_DEFAULT_AFTER = check_setting_int(settings.CFG, "General", "status_default_after", WANTED)
        if settings.STATUS_DEFAULT_AFTER not in (SKIPPED, WANTED, IGNORED):
            settings.STATUS_DEFAULT_AFTER = WANTED
        settings.VERSION_NOTIFY = check_setting_bool(settings.CFG, "General", "version_notify", True)
        settings.AUTO_UPDATE = check_setting_bool(settings.CFG, "General", "auto_update")
        settings.NOTIFY_ON_UPDATE = check_setting_bool(settings.CFG, "General", "notify_on_update", True)
        settings.SEASON_FOLDERS_DEFAULT = check_setting_bool(settings.CFG, "General", "season_folders_default", True)

        settings.ANIME_DEFAULT = check_setting_bool(settings.CFG, "General", "anime_default")
        settings.SCENE_DEFAULT = check_setting_bool(settings.CFG, "General", "scene_default")

        settings.PROVIDER_ORDER = check_setting_str(settings.CFG, "General", "provider_order").split()

        settings.NAMING_PATTERN = check_setting_str(settings.CFG, "General", "naming_pattern", "Season %0S/%SN - S%0SE%0E - %EN")
        settings.NAMING_ABD_PATTERN = check_setting_str(settings.CFG, "General", "naming_abd_pattern", "%SN - %A.D - %EN")
        settings.NAMING_CUSTOM_ABD = check_setting_bool(settings.CFG, "General", "naming_custom_abd")
        settings.NAMING_SPORTS_PATTERN = check_setting_str(settings.CFG, "General", "naming_sports_pattern", "%SN - %A-D - %EN")
        settings.NAMING_ANIME_PATTERN = check_setting_str(settings.CFG, "General", "naming_anime_pattern", "Season %0S/%SN - S%0SE%0E - %EN")
        settings.NAMING_ANIME = check_setting_int(settings.CFG, "General", "naming_anime", 3, min_val=1, max_val=3)
        settings.NAMING_CUSTOM_SPORTS = check_setting_bool(settings.CFG, "General", "naming_custom_sports")
        settings.NAMING_CUSTOM_ANIME = check_setting_bool(settings.CFG, "General", "naming_custom_anime")
        settings.NAMING_MULTI_EP = check_setting_int(settings.CFG, "General", "naming_multi_ep", 1, min_val=1, max_val=max(MULTI_EP_STRINGS))
        settings.NAMING_ANIME_MULTI_EP = check_setting_int(settings.CFG, "General", "naming_anime_multi_ep", 1, min_val=1, max_val=max(MULTI_EP_STRINGS))
        settings.NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        settings.NAMING_STRIP_YEAR = check_setting_bool(settings.CFG, "General", "naming_strip_year")
        settings.NAMING_NO_BRACKETS = check_setting_bool(settings.CFG, "General", "naming_no_brackets")

        settings.USE_NZBS = check_setting_bool(settings.CFG, "General", "use_nzbs", settings.USE_NZBS)
        settings.USE_TORRENTS = check_setting_bool(settings.CFG, "General", "use_torrents", settings.USE_TORRENTS)

        settings.NZB_METHOD = check_setting_str(settings.CFG, "General", "nzb_method", "blackhole")
        if settings.NZB_METHOD not in ("blackhole", "sabnzbd", "nzbget", "download_station"):
            settings.NZB_METHOD = "blackhole"

        settings.TORRENT_METHOD = check_setting_str(settings.CFG, "General", "torrent_method", "blackhole")
        if settings.TORRENT_METHOD not in clients.getClientListDict(True):
            settings.TORRENT_METHOD = "blackhole"

        settings.DOWNLOAD_PROPERS = check_setting_bool(settings.CFG, "General", "download_propers", True)
        settings.CHECK_PROPERS_INTERVAL = check_setting_str(settings.CFG, "General", "check_propers_interval")
        if settings.CHECK_PROPERS_INTERVAL not in ("15m", "45m", "90m", "4h", "daily"):
            settings.CHECK_PROPERS_INTERVAL = "daily"

        settings.RANDOMIZE_PROVIDERS = check_setting_bool(settings.CFG, "General", "randomize_providers")

        settings.ALLOW_HIGH_PRIORITY = check_setting_bool(settings.CFG, "General", "allow_high_priority", True)

        settings.SKIP_REMOVED_FILES = check_setting_bool(settings.CFG, "General", "skip_removed_files")

        settings.ALLOWED_EXTENSIONS = check_setting_str(settings.CFG, "General", "allowed_extensions", settings.ALLOWED_EXTENSIONS)

        settings.USENET_RETENTION = check_setting_int(settings.CFG, "General", "usenet_retention", 500)
        settings.CACHE_RETENTION = check_setting_int(settings.CFG, "General", "cache_retention", 30)

        settings.AUTOPOSTPROCESSOR_FREQUENCY = check_setting_int(
            settings.CFG,
            "General",
            "autopostprocessor_frequency",
            settings.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY,
            min_val=settings.MIN_AUTOPOSTPROCESSOR_FREQUENCY,
            fallback_def=False,
        )

        settings.DAILYSEARCH_FREQUENCY = check_setting_int(
            settings.CFG,
            "General",
            "dailysearch_frequency",
            settings.DEFAULT_DAILYSEARCH_FREQUENCY,
            min_val=settings.MIN_DAILYSEARCH_FREQUENCY,
            fallback_def=False,
        )

        settings.MIN_BACKLOG_FREQUENCY = settings.get_backlog_cycle_time()
        settings.BACKLOG_FREQUENCY = check_setting_int(
            settings.CFG, "General", "backlog_frequency", settings.DEFAULT_BACKLOG_FREQUENCY, min_val=settings.MIN_BACKLOG_FREQUENCY, fallback_def=False
        )

        settings.UPDATE_FREQUENCY = check_setting_int(
            settings.CFG, "General", "update_frequency", settings.DEFAULT_UPDATE_FREQUENCY, min_val=settings.MIN_UPDATE_FREQUENCY, fallback_def=False
        )

        settings.SHOWUPDATE_HOUR = check_setting_int(settings.CFG, "General", "showupdate_hour", settings.DEFAULT_SHOWUPDATE_HOUR, min_val=0, max_val=23)

        settings.BACKLOG_DAYS = check_setting_int(settings.CFG, "General", "backlog_days", 7)

        settings.NEWS_LAST_READ = check_setting_str(settings.CFG, "General", "news_last_read", "1970-01-01")
        settings.NEWS_LATEST = settings.NEWS_LAST_READ

        settings.NZB_DIR = check_setting_str(settings.CFG, "Blackhole", "nzb_dir")
        settings.TORRENT_DIR = check_setting_str(settings.CFG, "Blackhole", "torrent_dir")

        settings.TV_DOWNLOAD_DIR = check_setting_str(settings.CFG, "General", "tv_download_dir")
        settings.PROCESS_AUTOMATICALLY = check_setting_bool(settings.CFG, "General", "process_automatically")
        settings.NO_DELETE = check_setting_bool(settings.CFG, "General", "no_delete")
        settings.USE_ICACLS = check_setting_bool(settings.CFG, "General", "use_icacls", True)
        settings.UNPACK = check_setting_int(settings.CFG, "General", "unpack", min_val=0, max_val=2)
        settings.UNPACK_DIR = check_setting_str(settings.CFG, "General", "unpack_dir")

        config.change_unrar_tool(
            check_setting_str(settings.CFG, "General", "unrar_tool", rarfile.UNRAR_TOOL),
            check_setting_str(settings.CFG, "General", "unar_tool", rarfile.UNAR_TOOL),
        )

        settings.RENAME_EPISODES = check_setting_bool(settings.CFG, "General", "rename_episodes", True)
        settings.AIRDATE_EPISODES = check_setting_bool(settings.CFG, "General", "airdate_episodes")
        settings.FILE_TIMESTAMP_TIMEZONE = check_setting_str(settings.CFG, "General", "file_timestamp_timezone", "network")
        settings.KEEP_PROCESSED_DIR = check_setting_bool(settings.CFG, "General", "keep_processed_dir", True)
        settings.PROCESS_METHOD = check_setting_str(settings.CFG, "General", "process_method", "copy" if settings.KEEP_PROCESSED_DIR else "move")
        settings.PROCESSOR_FOLLOW_SYMLINKS = check_setting_bool(settings.CFG, "General", "processor_follow_symlinks")
        settings.DELRARCONTENTS = check_setting_bool(settings.CFG, "General", "del_rar_contents")
        settings.MOVE_ASSOCIATED_FILES = check_setting_bool(settings.CFG, "General", "move_associated_files")
        settings.DELETE_NON_ASSOCIATED_FILES = check_setting_bool(settings.CFG, "General", "delete_non_associated_files", True)
        settings.POSTPONE_IF_SYNC_FILES = check_setting_bool(settings.CFG, "General", "postpone_if_sync_files", True)
        settings.SYNC_FILES = check_setting_str(settings.CFG, "General", "sync_files", settings.SYNC_FILES)
        settings.NFO_RENAME = check_setting_bool(settings.CFG, "General", "nfo_rename", True)
        settings.CREATE_MISSING_SHOW_DIRS = check_setting_bool(settings.CFG, "General", "create_missing_show_dirs")
        settings.ADD_SHOWS_WO_DIR = check_setting_bool(settings.CFG, "General", "add_shows_wo_dir")
        settings.ADD_SHOWS_WITH_YEAR = check_setting_bool(settings.CFG, "General", "add_shows_with_year")
        settings.USE_FREE_SPACE_CHECK = check_setting_bool(settings.CFG, "General", "use_free_space_check", True)

        settings.NZBS = check_setting_bool(settings.CFG, "NZBs", "nzbs")
        settings.NZBS_UID = check_setting_str(settings.CFG, "NZBs", "nzbs_uid", censor_log=True)
        settings.NZBS_HASH = check_setting_str(settings.CFG, "NZBs", "nzbs_hash", censor_log=True)

        settings.NEWZBIN = check_setting_bool(settings.CFG, "Newzbin", "newzbin")
        settings.NEWZBIN_USERNAME = check_setting_str(settings.CFG, "Newzbin", "newzbin_username", censor_log=True)
        settings.NEWZBIN_PASSWORD = check_setting_str(settings.CFG, "Newzbin", "newzbin_password", censor_log=True)

        settings.SAB_USERNAME = check_setting_str(settings.CFG, "SABnzbd", "sab_username", censor_log=True)
        settings.SAB_PASSWORD = check_setting_str(settings.CFG, "SABnzbd", "sab_password", censor_log=True)
        settings.SAB_APIKEY = check_setting_str(settings.CFG, "SABnzbd", "sab_apikey", censor_log=True)
        settings.SAB_CATEGORY = check_setting_str(settings.CFG, "SABnzbd", "sab_category", "tv")
        settings.SAB_CATEGORY_BACKLOG = check_setting_str(settings.CFG, "SABnzbd", "sab_category_backlog", settings.SAB_CATEGORY)
        settings.SAB_CATEGORY_ANIME = check_setting_str(settings.CFG, "SABnzbd", "sab_category_anime", "anime")
        settings.SAB_CATEGORY_ANIME_BACKLOG = check_setting_str(settings.CFG, "SABnzbd", "sab_category_anime_backlog", settings.SAB_CATEGORY_ANIME)
        settings.SAB_HOST = check_setting_str(settings.CFG, "SABnzbd", "sab_host")
        settings.SAB_FORCED = check_setting_bool(settings.CFG, "SABnzbd", "sab_forced")

        settings.NZBGET_USERNAME = check_setting_str(settings.CFG, "NZBget", "nzbget_username", "nzbget", censor_log=True)
        settings.NZBGET_PASSWORD = check_setting_str(settings.CFG, "NZBget", "nzbget_password", "tegbzn6789", censor_log=True)
        settings.NZBGET_CATEGORY = check_setting_str(settings.CFG, "NZBget", "nzbget_category", "tv")
        settings.NZBGET_CATEGORY_BACKLOG = check_setting_str(settings.CFG, "NZBget", "nzbget_category_backlog", settings.NZBGET_CATEGORY)
        settings.NZBGET_CATEGORY_ANIME = check_setting_str(settings.CFG, "NZBget", "nzbget_category_anime", "anime")
        settings.NZBGET_CATEGORY_ANIME_BACKLOG = check_setting_str(settings.CFG, "NZBget", "nzbget_category_anime_backlog", settings.NZBGET_CATEGORY_ANIME)
        settings.NZBGET_HOST = check_setting_str(settings.CFG, "NZBget", "nzbget_host")
        settings.NZBGET_USE_HTTPS = check_setting_bool(settings.CFG, "NZBget", "nzbget_use_https")
        settings.NZBGET_PRIORITY = check_setting_int(settings.CFG, "NZBget", "nzbget_priority", 100)
        if settings.NZBGET_PRIORITY not in (-100, -50, 0, 50, 100, 900):
            settings.NZBGET_PRIORITY = 100

        settings.TORRENT_USERNAME = check_setting_str(settings.CFG, "TORRENT", "torrent_username", censor_log=True)
        settings.TORRENT_PASSWORD = check_setting_str(settings.CFG, "TORRENT", "torrent_password", censor_log=True)
        settings.TORRENT_HOST = check_setting_str(settings.CFG, "TORRENT", "torrent_host")
        settings.TORRENT_PATH = check_setting_str(settings.CFG, "TORRENT", "torrent_path")
        settings.TORRENT_PATH_INCOMPLETE = check_setting_str(settings.CFG, "TORRENT", "torrent_path_incomplete")

        # Fix duplicated options
        if settings.TORRENT_METHOD.startswith("deluge"):
            deluge_download_dir = check_setting_str(settings.CFG, "TORRENT", "torrent_download_dir_deluge")
            deluge_complete_dir = check_setting_str(settings.CFG, "TORRENT", "torrent_complete_dir_deluge")
            settings.TORRENT_PATH = deluge_complete_dir or settings.TORRENT_PATH
            if deluge_download_dir and not settings.TORRENT_PATH_INCOMPLETE:
                settings.TORRENT_PATH_INCOMPLETE = deluge_download_dir

        settings.TORRENT_SEED_TIME = check_setting_int(settings.CFG, "TORRENT", "torrent_seed_time", min_val=-1)
        settings.TORRENT_PAUSED = check_setting_bool(settings.CFG, "TORRENT", "torrent_paused")
        settings.TORRENT_HIGH_BANDWIDTH = check_setting_bool(settings.CFG, "TORRENT", "torrent_high_bandwidth")
        settings.TORRENT_LABEL = check_setting_str(settings.CFG, "TORRENT", "torrent_label")
        settings.TORRENT_LABEL_ANIME = check_setting_str(settings.CFG, "TORRENT", "torrent_label_anime")
        settings.TORRENT_VERIFY_CERT = check_setting_bool(settings.CFG, "TORRENT", "torrent_verify_cert")
        settings.TORRENT_RPCURL = check_setting_str(settings.CFG, "TORRENT", "torrent_rpcurl", "transmission")
        settings.TORRENT_AUTH_TYPE = check_setting_str(settings.CFG, "TORRENT", "torrent_auth_type")

        settings.SYNOLOGY_DSM_HOST = check_setting_str(settings.CFG, "Synology", "host")
        settings.SYNOLOGY_DSM_USERNAME = check_setting_str(settings.CFG, "Synology", "username", censor_log=True)
        settings.SYNOLOGY_DSM_PASSWORD = check_setting_str(settings.CFG, "Synology", "password", censor_log=True)
        settings.SYNOLOGY_DSM_PATH = check_setting_str(settings.CFG, "Synology", "path")

        helpers.manage_torrents_url(reset=True)

        settings.USE_KODI = check_setting_bool(settings.CFG, "KODI", "use_kodi")
        settings.KODI_ALWAYS_ON = check_setting_bool(settings.CFG, "KODI", "kodi_always_on", True)
        settings.KODI_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "KODI", "kodi_notify_onsnatch")
        settings.KODI_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "KODI", "kodi_notify_ondownload")
        settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "KODI", "kodi_notify_onsubtitledownload")
        settings.KODI_UPDATE_LIBRARY = check_setting_bool(settings.CFG, "KODI", "kodi_update_library")
        settings.KODI_UPDATE_FULL = check_setting_bool(settings.CFG, "KODI", "kodi_update_full")
        settings.KODI_UPDATE_ONLYFIRST = check_setting_bool(settings.CFG, "KODI", "kodi_update_onlyfirst")
        settings.KODI_HOST = check_setting_str(settings.CFG, "KODI", "kodi_host")
        settings.KODI_USERNAME = check_setting_str(settings.CFG, "KODI", "kodi_username", censor_log=True)
        settings.KODI_PASSWORD = check_setting_str(settings.CFG, "KODI", "kodi_password", censor_log=True)

        settings.USE_PLEX_SERVER = check_setting_bool(settings.CFG, "Plex", "use_plex_server")
        settings.PLEX_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Plex", "plex_notify_onsnatch")
        settings.PLEX_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Plex", "plex_notify_ondownload")
        settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Plex", "plex_notify_onsubtitledownload")
        settings.PLEX_UPDATE_LIBRARY = check_setting_bool(settings.CFG, "Plex", "plex_update_library")
        settings.PLEX_SERVER_HOST = check_setting_str(settings.CFG, "Plex", "plex_server_host")
        settings.PLEX_SERVER_TOKEN = check_setting_str(settings.CFG, "Plex", "plex_server_token")
        settings.PLEX_CLIENT_HOST = check_setting_str(settings.CFG, "Plex", "plex_client_host")
        settings.PLEX_SERVER_USERNAME = check_setting_str(settings.CFG, "Plex", "plex_server_username", censor_log=True)
        settings.PLEX_SERVER_PASSWORD = check_setting_str(settings.CFG, "Plex", "plex_server_password", censor_log=True)
        settings.USE_PLEX_CLIENT = check_setting_bool(settings.CFG, "Plex", "use_plex_client")
        settings.PLEX_CLIENT_USERNAME = check_setting_str(settings.CFG, "Plex", "plex_client_username", censor_log=True)
        settings.PLEX_CLIENT_PASSWORD = check_setting_str(settings.CFG, "Plex", "plex_client_password", censor_log=True)
        settings.PLEX_SERVER_HTTPS = check_setting_bool(settings.CFG, "Plex", "plex_server_https")

        settings.USE_EMBY = check_setting_bool(settings.CFG, "Emby", "use_emby")
        settings.EMBY_HOST = check_setting_str(settings.CFG, "Emby", "emby_host")
        settings.EMBY_APIKEY = check_setting_str(settings.CFG, "Emby", "emby_apikey")

        settings.USE_GROWL = check_setting_bool(settings.CFG, "Growl", "use_growl")
        settings.GROWL_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Growl", "growl_notify_onsnatch")
        settings.GROWL_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Growl", "growl_notify_ondownload")
        settings.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Growl", "growl_notify_onsubtitledownload")
        settings.GROWL_HOST = check_setting_str(settings.CFG, "Growl", "growl_host")
        settings.GROWL_PASSWORD = check_setting_str(settings.CFG, "Growl", "growl_password", censor_log=True)

        settings.USE_FREEMOBILE = check_setting_bool(settings.CFG, "FreeMobile", "use_freemobile")
        settings.FREEMOBILE_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "FreeMobile", "freemobile_notify_onsnatch")
        settings.FREEMOBILE_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "FreeMobile", "freemobile_notify_ondownload")
        settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "FreeMobile", "freemobile_notify_onsubtitledownload")
        settings.FREEMOBILE_ID = check_setting_str(settings.CFG, "FreeMobile", "freemobile_id")
        settings.FREEMOBILE_APIKEY = check_setting_str(settings.CFG, "FreeMobile", "freemobile_apikey")

        settings.FLARESOLVERR_URI = check_setting_str(settings.CFG, "General", "flaresolverr_uri")

        settings.USE_TELEGRAM = check_setting_bool(settings.CFG, "Telegram", "use_telegram")
        settings.TELEGRAM_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Telegram", "telegram_notify_onsnatch")
        settings.TELEGRAM_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Telegram", "telegram_notify_ondownload")
        settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Telegram", "telegram_notify_onsubtitledownload")
        settings.TELEGRAM_ID = check_setting_str(settings.CFG, "Telegram", "telegram_id")
        settings.TELEGRAM_APIKEY = check_setting_str(settings.CFG, "Telegram", "telegram_apikey")

        settings.USE_JOIN = check_setting_bool(settings.CFG, "Join", "use_join")
        settings.JOIN_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Join", "join_notify_onsnatch")
        settings.JOIN_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Join", "join_notify_ondownload")
        settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Join", "join_notify_onsubtitledownload")
        settings.JOIN_ID = check_setting_str(settings.CFG, "Join", "join_id")
        settings.JOIN_APIKEY = check_setting_str(settings.CFG, "Join", "join_apikey")

        settings.USE_PROWL = check_setting_bool(settings.CFG, "Prowl", "use_prowl")
        settings.PROWL_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Prowl", "prowl_notify_onsnatch")
        settings.PROWL_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Prowl", "prowl_notify_ondownload")
        settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Prowl", "prowl_notify_onsubtitledownload")
        settings.PROWL_API = check_setting_str(settings.CFG, "Prowl", "prowl_api", censor_log=True)
        settings.PROWL_PRIORITY = check_setting_str(settings.CFG, "Prowl", "prowl_priority", "0")
        settings.PROWL_MESSAGE_TITLE = check_setting_str(settings.CFG, "Prowl", "prowl_message_title", "SickChill")

        settings.USE_TWITTER = check_setting_bool(settings.CFG, "Twitter", "use_twitter")
        settings.TWITTER_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Twitter", "twitter_notify_onsnatch")
        settings.TWITTER_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Twitter", "twitter_notify_ondownload")
        settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Twitter", "twitter_notify_onsubtitledownload")
        settings.TWITTER_USERNAME = check_setting_str(settings.CFG, "Twitter", "twitter_username", censor_log=True)
        settings.TWITTER_PASSWORD = check_setting_str(settings.CFG, "Twitter", "twitter_password", censor_log=True)
        settings.TWITTER_PREFIX = check_setting_str(settings.CFG, "Twitter", "twitter_prefix", settings.GIT_REPO)
        settings.TWITTER_DMTO = check_setting_str(settings.CFG, "Twitter", "twitter_dmto")
        settings.TWITTER_USEDM = check_setting_bool(settings.CFG, "Twitter", "twitter_usedm")

        settings.USE_TWILIO = check_setting_bool(settings.CFG, "Twilio", "use_twilio")
        settings.TWILIO_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Twilio", "twilio_notify_onsnatch")
        settings.TWILIO_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Twilio", "twilio_notify_ondownload")
        settings.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Twilio", "twilio_notify_onsubtitledownload")
        settings.TWILIO_PHONE_SID = check_setting_str(settings.CFG, "Twilio", "twilio_phone_sid", censor_log=True)
        settings.TWILIO_ACCOUNT_SID = check_setting_str(settings.CFG, "Twilio", "twilio_account_sid", censor_log=True)
        settings.TWILIO_AUTH_TOKEN = check_setting_str(settings.CFG, "Twilio", "twilio_auth_token", censor_log=True)
        settings.TWILIO_TO_NUMBER = check_setting_str(settings.CFG, "Twilio", "twilio_to_number", censor_log=True)

        settings.USE_BOXCAR2 = check_setting_bool(settings.CFG, "Boxcar2", "use_boxcar2")
        settings.BOXCAR2_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Boxcar2", "boxcar2_notify_onsnatch")
        settings.BOXCAR2_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Boxcar2", "boxcar2_notify_ondownload")
        settings.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Boxcar2", "boxcar2_notify_onsubtitledownload")
        settings.BOXCAR2_ACCESSTOKEN = check_setting_str(settings.CFG, "Boxcar2", "boxcar2_accesstoken", censor_log=True)

        settings.USE_PUSHOVER = check_setting_bool(settings.CFG, "Pushover", "use_pushover")
        settings.PUSHOVER_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Pushover", "pushover_notify_onsnatch")
        settings.PUSHOVER_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Pushover", "pushover_notify_ondownload")
        settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Pushover", "pushover_notify_onsubtitledownload")
        settings.PUSHOVER_USERKEY = check_setting_str(settings.CFG, "Pushover", "pushover_userkey", censor_log=True)
        settings.PUSHOVER_APIKEY = check_setting_str(settings.CFG, "Pushover", "pushover_apikey", censor_log=True)
        settings.PUSHOVER_DEVICE = check_setting_str(settings.CFG, "Pushover", "pushover_device")
        settings.PUSHOVER_SOUND = check_setting_str(settings.CFG, "Pushover", "pushover_sound", "pushover")
        settings.PUSHOVER_PRIORITY = check_setting_str(settings.CFG, "Pushover", "pushover_priority", "0")

        settings.USE_LIBNOTIFY = check_setting_bool(settings.CFG, "Libnotify", "use_libnotify")
        settings.LIBNOTIFY_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Libnotify", "libnotify_notify_onsnatch")
        settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Libnotify", "libnotify_notify_ondownload")
        settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Libnotify", "libnotify_notify_onsubtitledownload")

        settings.USE_NMJ = check_setting_bool(settings.CFG, "NMJ", "use_nmj")
        settings.NMJ_HOST = check_setting_str(settings.CFG, "NMJ", "nmj_host")
        settings.NMJ_DATABASE = check_setting_str(settings.CFG, "NMJ", "nmj_database")
        settings.NMJ_MOUNT = check_setting_str(settings.CFG, "NMJ", "nmj_mount")

        settings.USE_NMJv2 = check_setting_bool(settings.CFG, "NMJv2", "use_nmjv2")
        settings.NMJv2_HOST = check_setting_str(settings.CFG, "NMJv2", "nmjv2_host")
        settings.NMJv2_DATABASE = check_setting_str(settings.CFG, "NMJv2", "nmjv2_database")
        settings.NMJv2_DBLOC = check_setting_str(settings.CFG, "NMJv2", "nmjv2_dbloc")

        settings.USE_SYNOINDEX = check_setting_bool(settings.CFG, "Synology", "use_synoindex")

        settings.USE_SYNOLOGYNOTIFIER = check_setting_bool(settings.CFG, "SynologyNotifier", "use_synologynotifier")
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "SynologyNotifier", "synologynotifier_notify_onsnatch")
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "SynologyNotifier", "synologynotifier_notify_ondownload")
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "SynologyNotifier", "synologynotifier_notify_onsubtitledownload")

        settings.USE_SLACK = check_setting_bool(settings.CFG, "Slack", "use_slack")
        settings.SLACK_NOTIFY_SNATCH = check_setting_bool(settings.CFG, "Slack", "slack_notify_snatch")
        settings.SLACK_NOTIFY_DOWNLOAD = check_setting_bool(settings.CFG, "Slack", "slack_notify_download")
        settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Slack", "slack_notify_subtitledownload")
        settings.SLACK_WEBHOOK = check_setting_str(settings.CFG, "Slack", "slack_webhook")
        settings.SLACK_ICON_EMOJI = check_setting_str(settings.CFG, "Slack", "slack_icon_emoji")

        settings.USE_ROCKETCHAT = check_setting_bool(settings.CFG, "RocketChat", "use_rocketchat")
        settings.ROCKETCHAT_NOTIFY_SNATCH = check_setting_bool(settings.CFG, "RocketChat", "rocketchat_notify_snatch")
        settings.ROCKETCHAT_NOTIFY_DOWNLOAD = check_setting_bool(settings.CFG, "RocketChat", "rocketchat_notify_download")
        settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "RocketChat", "rocketchat_notify_subtitledownload")
        settings.ROCKETCHAT_WEBHOOK = check_setting_str(settings.CFG, "RocketChat", "rocketchat_webhook")
        settings.ROCKETCHAT_ICON_EMOJI = check_setting_str(settings.CFG, "RocketChat", "rocketchat_icon_emoji")

        settings.USE_MATRIX = check_setting_bool(settings.CFG, "Matrix", "use_matrix")
        settings.MATRIX_NOTIFY_SNATCH = check_setting_bool(settings.CFG, "Matrix", "matrix_notify_snatch")
        settings.MATRIX_NOTIFY_DOWNLOAD = check_setting_bool(settings.CFG, "Matrix", "matrix_notify_download")
        settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Matrix", "matrix_notify_subtitledownload")
        settings.MATRIX_API_TOKEN = check_setting_str(settings.CFG, "Matrix", "matrix_api_token")
        settings.MATRIX_SERVER = check_setting_str(settings.CFG, "Matrix", "matrix_server")
        settings.MATRIX_ROOM = check_setting_str(settings.CFG, "Matrix", "matrix_room")

        settings.USE_DISCORD = check_setting_bool(settings.CFG, "Discord", "use_discord")
        settings.DISCORD_NOTIFY_SNATCH = check_setting_bool(settings.CFG, "Discord", "discord_notify_snatch")
        settings.DISCORD_NOTIFY_DOWNLOAD = check_setting_bool(settings.CFG, "Discord", "discord_notify_download")
        settings.DISCORD_WEBHOOK = check_setting_str(settings.CFG, "Discord", "discord_webhook")
        settings.DISCORD_NAME = check_setting_str(settings.CFG, "Discord", "discord_name")
        settings.DISCORD_AVATAR_URL = check_setting_str(settings.CFG, "Discord", "discord_avatar_url")
        settings.DISCORD_TTS = check_setting_str(settings.CFG, "Discord", "discord_tts")

        settings.USE_TRAKT = check_setting_bool(settings.CFG, "Trakt", "use_trakt")
        settings.TRAKT_USERNAME = check_setting_str(settings.CFG, "Trakt", "trakt_username", censor_log=True)
        settings.TRAKT_ACCESS_TOKEN = check_setting_str(settings.CFG, "Trakt", "trakt_access_token", censor_log=True)
        settings.TRAKT_REFRESH_TOKEN = check_setting_str(settings.CFG, "Trakt", "trakt_refresh_token", censor_log=True)
        settings.TRAKT_REMOVE_WATCHLIST = check_setting_bool(settings.CFG, "Trakt", "trakt_remove_watchlist")
        settings.TRAKT_REMOVE_SERIESLIST = check_setting_bool(settings.CFG, "Trakt", "trakt_remove_serieslist")
        settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL = check_setting_bool(settings.CFG, "Trakt", "trakt_remove_show_from_sickchill")
        settings.TRAKT_SYNC_WATCHLIST = check_setting_bool(settings.CFG, "Trakt", "trakt_sync_watchlist")
        settings.TRAKT_METHOD_ADD = check_setting_int(settings.CFG, "Trakt", "trakt_method_add", min_val=0, max_val=2)
        settings.TRAKT_START_PAUSED = check_setting_bool(settings.CFG, "Trakt", "trakt_start_paused")
        settings.TRAKT_USE_RECOMMENDED = check_setting_bool(settings.CFG, "Trakt", "trakt_use_recommended")
        settings.TRAKT_SYNC = check_setting_bool(settings.CFG, "Trakt", "trakt_sync")
        settings.TRAKT_SYNC_REMOVE = check_setting_bool(settings.CFG, "Trakt", "trakt_sync_remove")
        settings.TRAKT_DEFAULT_INDEXER = check_setting_int(settings.CFG, "Trakt", "trakt_default_indexer", 1, min_val=1, max_val=2)
        settings.TRAKT_TIMEOUT = check_setting_int(settings.CFG, "Trakt", "trakt_timeout", 30, min_val=0)
        settings.TRAKT_BLACKLIST_NAME = check_setting_str(settings.CFG, "Trakt", "trakt_blacklist_name")

        settings.USE_PYTIVO = check_setting_bool(settings.CFG, "pyTivo", "use_pytivo")
        settings.PYTIVO_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "pyTivo", "pytivo_notify_onsnatch")
        settings.PYTIVO_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "pyTivo", "pytivo_notify_ondownload")
        settings.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "pyTivo", "pytivo_notify_onsubtitledownload")
        settings.PYTIVO_UPDATE_LIBRARY = check_setting_bool(settings.CFG, "pyTivo", "pyTivo_update_library")
        settings.PYTIVO_HOST = check_setting_str(settings.CFG, "pyTivo", "pytivo_host")
        settings.PYTIVO_SHARE_NAME = check_setting_str(settings.CFG, "pyTivo", "pytivo_share_name")
        settings.PYTIVO_TIVO_NAME = check_setting_str(settings.CFG, "pyTivo", "pytivo_tivo_name")

        settings.USE_NMA = check_setting_bool(settings.CFG, "NMA", "use_nma")
        settings.NMA_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "NMA", "nma_notify_onsnatch")
        settings.NMA_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "NMA", "nma_notify_ondownload")
        settings.NMA_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "NMA", "nma_notify_onsubtitledownload")
        settings.NMA_API = check_setting_str(settings.CFG, "NMA", "nma_api", censor_log=True)
        settings.NMA_PRIORITY = check_setting_str(settings.CFG, "NMA", "nma_priority", "0")

        settings.USE_PUSHALOT = check_setting_bool(settings.CFG, "Pushalot", "use_pushalot")
        settings.PUSHALOT_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Pushalot", "pushalot_notify_onsnatch")
        settings.PUSHALOT_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Pushalot", "pushalot_notify_ondownload")
        settings.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Pushalot", "pushalot_notify_onsubtitledownload")
        settings.PUSHALOT_AUTHORIZATIONTOKEN = check_setting_str(settings.CFG, "Pushalot", "pushalot_authorizationtoken", censor_log=True)

        settings.USE_PUSHBULLET = check_setting_bool(settings.CFG, "Pushbullet", "use_pushbullet")
        settings.PUSHBULLET_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Pushbullet", "pushbullet_notify_onsnatch")
        settings.PUSHBULLET_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Pushbullet", "pushbullet_notify_ondownload")
        settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Pushbullet", "pushbullet_notify_onsubtitledownload")
        settings.PUSHBULLET_API = check_setting_str(settings.CFG, "Pushbullet", "pushbullet_api", censor_log=True)
        settings.PUSHBULLET_DEVICE = check_setting_str(settings.CFG, "Pushbullet", "pushbullet_device")
        settings.PUSHBULLET_CHANNEL = check_setting_str(settings.CFG, "Pushbullet", "pushbullet_channel")

        settings.USE_EMAIL = check_setting_bool(settings.CFG, "Email", "use_email")
        settings.EMAIL_NOTIFY_ONSNATCH = check_setting_bool(settings.CFG, "Email", "email_notify_onsnatch")
        settings.EMAIL_NOTIFY_ONDOWNLOAD = check_setting_bool(settings.CFG, "Email", "email_notify_ondownload")
        settings.EMAIL_NOTIFY_ONPOSTPROCESS = check_setting_bool(settings.CFG, "Email", "email_notify_onpostprocess")
        settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(settings.CFG, "Email", "email_notify_onsubtitledownload")
        settings.EMAIL_HOST = check_setting_str(settings.CFG, "Email", "email_host")
        settings.EMAIL_PORT = check_setting_int(settings.CFG, "Email", "email_port", 25, min_val=21, max_val=65535)
        settings.EMAIL_TLS = check_setting_bool(settings.CFG, "Email", "email_tls")
        settings.EMAIL_USER = check_setting_str(settings.CFG, "Email", "email_user", censor_log=True)
        settings.EMAIL_PASSWORD = check_setting_str(settings.CFG, "Email", "email_password", censor_log=True)
        settings.EMAIL_FROM = check_setting_str(settings.CFG, "Email", "email_from")
        settings.EMAIL_LIST = check_setting_str(settings.CFG, "Email", "email_list")
        settings.EMAIL_SUBJECT = check_setting_str(settings.CFG, "Email", "email_subject")

        settings.USE_SUBTITLES = check_setting_bool(settings.CFG, "Subtitles", "use_subtitles")
        settings.SUBTITLES_INCLUDE_SPECIALS = check_setting_bool(settings.CFG, "Subtitles", "subtitles_include_specials", True)
        settings.SUBTITLES_LANGUAGES = check_setting_str(settings.CFG, "Subtitles", "subtitles_languages").split(",")
        if settings.SUBTITLES_LANGUAGES[0] == "":
            settings.SUBTITLES_LANGUAGES = []
        settings.SUBTITLES_DIR = check_setting_str(settings.CFG, "Subtitles", "subtitles_dir")
        settings.SUBTITLES_SERVICES_LIST = check_setting_str(settings.CFG, "Subtitles", "SUBTITLES_SERVICES_LIST").split(",")
        settings.SUBTITLES_SERVICES_ENABLED = [int(x) for x in check_setting_str(settings.CFG, "Subtitles", "SUBTITLES_SERVICES_ENABLED").split("|") if x]
        settings.SUBTITLES_DEFAULT = check_setting_bool(settings.CFG, "Subtitles", "subtitles_default")
        settings.SUBTITLES_HISTORY = check_setting_bool(settings.CFG, "Subtitles", "subtitles_history")
        settings.SUBTITLES_PERFECT_MATCH = check_setting_bool(settings.CFG, "Subtitles", "subtitles_perfect_match", True)
        settings.EMBEDDED_SUBTITLES_ALL = check_setting_bool(settings.CFG, "Subtitles", "embedded_subtitles_all")
        settings.SUBTITLES_HEARING_IMPAIRED = check_setting_bool(settings.CFG, "Subtitles", "subtitles_hearing_impaired")
        settings.SUBTITLES_FINDER_FREQUENCY = check_setting_int(settings.CFG, "Subtitles", "subtitles_finder_frequency", 1, min_val=1)
        settings.SUBTITLES_MULTI = check_setting_bool(settings.CFG, "Subtitles", "subtitles_multi", True)
        settings.SUBTITLES_KEEP_ONLY_WANTED = check_setting_bool(settings.CFG, "Subtitles", "subtitles_keep_only_wanted")
        settings.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(settings.CFG, "Subtitles", "subtitles_extra_scripts").split("|") if x.strip()]

        settings.ADDIC7ED_USER = check_setting_str(settings.CFG, "Subtitles", "addic7ed_username", censor_log=True)
        settings.ADDIC7ED_PASS = check_setting_str(settings.CFG, "Subtitles", "addic7ed_password", censor_log=True)

        settings.ITASA_USER = check_setting_str(settings.CFG, "Subtitles", "itasa_username", censor_log=True)
        settings.ITASA_PASS = check_setting_str(settings.CFG, "Subtitles", "itasa_password", censor_log=True)

        settings.LEGENDASTV_USER = check_setting_str(settings.CFG, "Subtitles", "legendastv_username", censor_log=True)
        settings.LEGENDASTV_PASS = check_setting_str(settings.CFG, "Subtitles", "legendastv_password", censor_log=True)

        settings.OPENSUBTITLES_USER = check_setting_str(settings.CFG, "Subtitles", "opensubtitles_username", censor_log=True)
        settings.OPENSUBTITLES_PASS = check_setting_str(settings.CFG, "Subtitles", "opensubtitles_password", censor_log=True)

        settings.SUBSCENTER_USER = check_setting_str(settings.CFG, "Subtitles", "subscenter_username", censor_log=True)
        settings.SUBSCENTER_PASS = check_setting_str(settings.CFG, "Subtitles", "subscenter_password", censor_log=True)

        settings.USE_FAILED_DOWNLOADS = check_setting_bool(settings.CFG, "FailedDownloads", "use_failed_downloads")
        settings.DELETE_FAILED = check_setting_bool(settings.CFG, "FailedDownloads", "delete_failed")

        settings.BACKLOG_MISSING_ONLY = check_setting_bool(settings.CFG, "General", "backlog_missing_only")

        settings.IGNORE_WORDS = check_setting_str(settings.CFG, "General", "ignore_words", settings.IGNORE_WORDS)
        settings.TRACKERS_LIST = check_setting_str(settings.CFG, "General", "trackers_list", settings.TRACKERS_LIST)
        settings.REQUIRE_WORDS = check_setting_str(settings.CFG, "General", "require_words", settings.REQUIRE_WORDS)
        settings.PREFER_WORDS = check_setting_str(settings.CFG, "General", "prefer_words", settings.PREFER_WORDS)
        settings.IGNORED_SUBS_LIST = check_setting_str(settings.CFG, "General", "ignored_subs_list", settings.IGNORED_SUBS_LIST)

        settings.CALENDAR_UNPROTECTED = check_setting_bool(settings.CFG, "General", "calendar_unprotected")
        settings.CALENDAR_ICONS = check_setting_bool(settings.CFG, "General", "calendar_icons")

        settings.NO_RESTART = check_setting_bool(settings.CFG, "General", "no_restart")

        settings.EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(settings.CFG, "General", "extra_scripts").split("|") if x.strip()]

        settings.USE_LISTVIEW = check_setting_bool(settings.CFG, "General", "use_listview")

        settings.ANIMESUPPORT = False
        settings.USE_ANIDB = check_setting_bool(settings.CFG, "ANIDB", "use_anidb")
        settings.ANIDB_USERNAME = check_setting_str(settings.CFG, "ANIDB", "anidb_username", censor_log=True)
        settings.ANIDB_PASSWORD = check_setting_str(settings.CFG, "ANIDB", "anidb_password", censor_log=True)
        settings.ANIDB_USE_MYLIST = check_setting_bool(settings.CFG, "ANIDB", "anidb_use_mylist")

        settings.ANIME_SPLIT_HOME = check_setting_bool(settings.CFG, "ANIME", "anime_split_home")
        settings.ANIME_SPLIT_HOME_IN_TABS = check_setting_bool(settings.CFG, "ANIME", "anime_split_home_in_tabs")

        settings.METADATA_KODI = check_setting_str(settings.CFG, "General", "metadata_kodi", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_MEDIABROWSER = check_setting_str(settings.CFG, "General", "metadata_mediabrowser", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_PS3 = check_setting_str(settings.CFG, "General", "metadata_ps3", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_WDTV = check_setting_str(settings.CFG, "General", "metadata_wdtv", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_TIVO = check_setting_str(settings.CFG, "General", "metadata_tivo", "0|0|0|0|0|0|0|0|0|0")
        settings.METADATA_MEDE8ER = check_setting_str(settings.CFG, "General", "metadata_mede8er", "0|0|0|0|0|0|0|0|0|0")

        settings.HOME_LAYOUT = check_setting_str(settings.CFG, "GUI", "home_layout", "poster")
        settings.HISTORY_LAYOUT = check_setting_str(settings.CFG, "GUI", "history_layout", "detailed")
        settings.HISTORY_LIMIT = check_setting_str(settings.CFG, "GUI", "history_limit", "100")
        settings.DISPLAY_SHOW_SPECIALS = check_setting_bool(settings.CFG, "GUI", "display_show_specials", True)
        settings.COMING_EPS_LAYOUT = check_setting_str(settings.CFG, "GUI", "coming_eps_layout", "banner")
        settings.COMING_EPS_DISPLAY_PAUSED = check_setting_bool(settings.CFG, "GUI", "coming_eps_display_paused")
        settings.COMING_EPS_DISPLAY_SNATCHED = check_setting_bool(settings.CFG, "GUI", "coming_eps_display_snatched")
        settings.COMING_EPS_SORT = check_setting_str(settings.CFG, "GUI", "coming_eps_sort", "date")
        settings.COMING_EPS_MISSED_RANGE = check_setting_int(settings.CFG, "GUI", "coming_eps_missed_range", 7, min_val=0, max_val=42810, fallback_def=False)
        settings.FUZZY_DATING = check_setting_bool(settings.CFG, "GUI", "fuzzy_dating")
        settings.TRIM_ZERO = check_setting_bool(settings.CFG, "GUI", "trim_zero")
        settings.DATE_PRESET = check_setting_str(settings.CFG, "GUI", "date_preset", "%x")
        settings.TIME_PRESET_W_SECONDS = check_setting_str(settings.CFG, "GUI", "time_preset", "%I:%M:%S %p")
        settings.TIME_PRESET = settings.TIME_PRESET_W_SECONDS.replace(":%S", "")
        settings.TIMEZONE_DISPLAY = check_setting_str(settings.CFG, "GUI", "timezone_display", "local")
        settings.POSTER_SORTBY = check_setting_str(settings.CFG, "GUI", "poster_sortby", "name")
        settings.POSTER_SORTDIR = check_setting_int(settings.CFG, "GUI", "poster_sortdir", 1, min_val=0, max_val=1)
        settings.DISPLAY_ALL_SEASONS = check_setting_bool(settings.CFG, "General", "display_all_seasons", True)
        settings.ENDED_SHOWS_UPDATE_INTERVAL = check_setting_int(settings.CFG, "General", "ended_shows_update_interval", 7)
        settings.NO_LGMARGIN = check_setting_bool(settings.CFG, "GUI", "no_lgmargin", True)

        if check_section(settings.CFG, "Shares"):
            settings.WINDOWS_SHARES.update(settings.CFG["Shares"])

        # initialize NZB and TORRENT providers
        settings.providerList = providers.makeProviderList()

        settings.NEWZNAB_DATA = check_setting_str(settings.CFG, "Newznab", "newznab_data")
        settings.newznabProviderList = NewznabProvider.providers_list(settings.NEWZNAB_DATA)

        TORRENTRSS_DATA = check_setting_str(settings.CFG, "TorrentRss", "torrentrss_data")
        settings.torrentRssProviderList = TorrentRssProvider.providers_list(TORRENTRSS_DATA)

        # dynamically load provider settings
        for curProvider in providers.sortedProviderList():
            curProvider.enabled = (curProvider.can_daily or curProvider.can_backlog) and check_setting_bool(
                settings.CFG, curProvider.get_id().upper(), curProvider.get_id()
            )
            if hasattr(curProvider, "custom_url"):
                curProvider.custom_url = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_custom_url"), "", censor_log=True)
            if hasattr(curProvider, "api_key"):
                curProvider.api_key = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_api_key"), censor_log=True)
            if hasattr(curProvider, "hash"):
                curProvider.hash = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_hash"), censor_log=True)
            if hasattr(curProvider, "digest"):
                curProvider.digest = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_digest"), censor_log=True)
            if hasattr(curProvider, "username"):
                curProvider.username = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_username"), censor_log=True)
            if hasattr(curProvider, "password"):
                curProvider.password = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_password"), censor_log=True)
            if hasattr(curProvider, "passkey"):
                curProvider.passkey = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_passkey"), censor_log=True)
            if hasattr(curProvider, "pin"):
                curProvider.pin = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_pin"), censor_log=True)
            if hasattr(curProvider, "confirmed"):
                curProvider.confirmed = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_confirmed"), True)
            if hasattr(curProvider, "ranked"):
                curProvider.ranked = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_ranked"), True)
            if hasattr(curProvider, "engrelease"):
                curProvider.engrelease = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_engrelease"))
            if hasattr(curProvider, "onlyspasearch"):
                curProvider.onlyspasearch = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_onlyspasearch"))
            if hasattr(curProvider, "sorting"):
                curProvider.sorting = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_sorting"), "seeders")
            if hasattr(curProvider, "options"):
                curProvider.options = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_options"), "")
            if hasattr(curProvider, "ratio"):
                curProvider.ratio = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_ratio"), "")
            if hasattr(curProvider, "minseed"):
                curProvider.minseed = check_setting_int(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_minseed"), 1, min_val=0)
            if hasattr(curProvider, "minleech"):
                curProvider.minleech = check_setting_int(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_minleech"), 0, min_val=0)
            if hasattr(curProvider, "freeleech"):
                curProvider.freeleech = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_freeleech"))
            if hasattr(curProvider, "search_mode"):
                curProvider.search_mode = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_search_mode"), "eponly")
            if hasattr(curProvider, "search_fallback"):
                curProvider.search_fallback = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_search_fallback"))
            if hasattr(curProvider, "enable_daily"):
                curProvider.enable_daily = curProvider.can_daily and check_setting_bool(
                    settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_enable_daily"), True
                )
            if hasattr(curProvider, "enable_backlog"):
                curProvider.enable_backlog = curProvider.can_backlog and check_setting_bool(
                    settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_enable_backlog"), curProvider.can_backlog
                )
            if hasattr(curProvider, "cat"):
                curProvider.cat = check_setting_int(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_cat"), 0)
            if hasattr(curProvider, "subtitle"):
                curProvider.subtitle = check_setting_bool(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_subtitle"))
            if hasattr(curProvider, "cookies"):
                curProvider.cookies = check_setting_str(settings.CFG, curProvider.get_id().upper(), curProvider.get_id("_cookies"), censor_log=True)

        providers.check_enabled_providers()

        if not os.path.isfile(settings.CONFIG_FILE):
            logger.debug("Unable to find '" + settings.CONFIG_FILE + "', all settings will be default!")
            save_config()

        # initialize the main SB database
        main_db_con = db.DBConnection()
        db.upgrade_database(main_db_con, main.InitialSchema)

        # initialize the cache database
        cache_db_con = db.DBConnection("cache.db")
        db.upgrade_database(cache_db_con, cache.InitialSchema)

        # initialize the failed downloads database
        failed_db_con = db.DBConnection("failed.db")
        db.upgrade_database(failed_db_con, failed.InitialSchema)

        # fix up any db problems
        main_db_con = db.DBConnection()
        db.sanity_check_database(main_db_con, main.MainSanityCheck)

        # migrate the config if it needs it
        migrator = ConfigMigrator(settings.CFG)
        migrator.migrate_config()

        # initialize metadata_providers
        settings.metadata_provider_dict = {}
        for cur_metadata_tuple in [
            (settings.METADATA_KODI, metadata.kodi),
            (settings.METADATA_MEDIABROWSER, metadata.mediabrowser),
            (settings.METADATA_PS3, metadata.ps3),
            (settings.METADATA_WDTV, metadata.wdtv),
            (settings.METADATA_TIVO, metadata.tivo),
            (settings.METADATA_MEDE8ER, metadata.mede8er),
        ]:

            cur_metadata_config, cur_metadata_module = cur_metadata_tuple
            cur_metadata_class = cur_metadata_module.metadata_class()
            cur_metadata_class.set_config(cur_metadata_config)
            settings.metadata_provider_dict[cur_metadata_class.name] = cur_metadata_class

        # initialize schedulers
        # updaters
        settings.versionCheckScheduler = scheduler.Scheduler(
            update_manager.UpdateManager(), cycleTime=datetime.timedelta(hours=settings.UPDATE_FREQUENCY), threadName="CHECKVERSION", silent=False
        )

        settings.showQueueScheduler = scheduler.Scheduler(show_queue.ShowQueue(), cycleTime=datetime.timedelta(seconds=5), threadName="SHOWQUEUE")

        settings.showUpdateScheduler = scheduler.Scheduler(
            show_updater.ShowUpdater(),
            run_delay=datetime.timedelta(seconds=20),
            cycleTime=datetime.timedelta(hours=1),
            start_time=datetime.time(hour=settings.SHOWUPDATE_HOUR),
            threadName="SHOWUPDATER",
            silent=False,
        )

        # searchers
        settings.searchQueueScheduler = scheduler.Scheduler(
            search_queue.SearchQueue(), run_delay=datetime.timedelta(seconds=10), cycleTime=datetime.timedelta(seconds=5), threadName="SEARCHQUEUE"
        )

        settings.dailySearchScheduler = scheduler.Scheduler(
            dailysearcher.DailySearcher(),
            run_delay=datetime.timedelta(minutes=10),
            cycleTime=datetime.timedelta(minutes=settings.DAILYSEARCH_FREQUENCY),
            threadName="DAILYSEARCHER",
        )

        update_interval = datetime.timedelta(minutes=settings.BACKLOG_FREQUENCY)
        settings.backlogSearchScheduler = searchBacklog.BacklogSearchScheduler(
            searchBacklog.BacklogSearcher(), cycleTime=update_interval, threadName="BACKLOG", run_delay=update_interval
        )

        search_intervals = {"15m": 15, "45m": 45, "90m": 90, "4h": 4 * 60, "daily": 24 * 60}
        if settings.CHECK_PROPERS_INTERVAL in search_intervals:
            update_interval = datetime.timedelta(minutes=search_intervals[settings.CHECK_PROPERS_INTERVAL])
            run_at = None
        else:
            update_interval = datetime.timedelta(hours=1)
            run_at = datetime.time(hour=1)  # 1 AM

        settings.properFinderScheduler = scheduler.Scheduler(
            properFinder.ProperFinder(),
            cycleTime=update_interval,
            threadName="FINDPROPERS",
            start_time=run_at,
            run_delay=update_interval,
            silent=not settings.DOWNLOAD_PROPERS,
        )

        # processors
        settings.postProcessorTaskScheduler = scheduler.Scheduler(
            post_processing_queue.ProcessingQueue(),
            run_delay=datetime.timedelta(seconds=5),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="POSTPROCESSOR",
        )

        settings.autoPostProcessorScheduler = scheduler.Scheduler(
            post_processing_queue.PostProcessor(),
            run_delay=datetime.timedelta(minutes=5),
            cycleTime=datetime.timedelta(minutes=settings.AUTOPOSTPROCESSOR_FREQUENCY),
            threadName="POSTPROCESSOR",
            silent=not settings.PROCESS_AUTOMATICALLY,
        )

        settings.traktCheckerScheduler = scheduler.Scheduler(
            traktChecker.TraktChecker(),
            run_delay=datetime.timedelta(minutes=5),
            cycleTime=datetime.timedelta(hours=1),
            threadName="TRAKTCHECKER",
            silent=not settings.USE_TRAKT,
        )

        settings.subtitlesFinderScheduler = scheduler.Scheduler(
            subtitles.SubtitlesFinder(),
            run_delay=datetime.timedelta(minutes=10),
            cycleTime=datetime.timedelta(hours=settings.SUBTITLES_FINDER_FREQUENCY),
            threadName="FINDSUBTITLES",
            silent=not settings.USE_SUBTITLES,
        )

        # notifications
        settings.notificationsTaskScheduler = scheduler.Scheduler(
            notifications_queue.NotificationsQueue(),
            run_delay=datetime.timedelta(seconds=5),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="NOTIFICATIONS",
        )

        settings.__INITIALIZED__["0"] = True
        return True


def start():
    with settings.INIT_LOCK:
        if settings.__INITIALIZED__:
            # start sysetm events queue
            settings.events.start()

            # start the daily search scheduler
            settings.dailySearchScheduler.enable = True
            settings.dailySearchScheduler.start()

            # start the backlog scheduler
            settings.backlogSearchScheduler.enable = True
            settings.backlogSearchScheduler.start()

            # start the show updater
            settings.showUpdateScheduler.enable = True
            settings.showUpdateScheduler.start()

            # start the version checker
            settings.versionCheckScheduler.enable = True
            settings.versionCheckScheduler.start()

            # start the queue checker
            settings.showQueueScheduler.enable = True
            settings.showQueueScheduler.start()

            # start the search queue checker
            settings.searchQueueScheduler.enable = True
            settings.searchQueueScheduler.start()

            # start the proper finder
            settings.properFinderScheduler.enable = settings.DOWNLOAD_PROPERS
            settings.properFinderScheduler.start()

            settings.postProcessorTaskScheduler.enable = True
            settings.postProcessorTaskScheduler.start()

            # start the post processor
            settings.autoPostProcessorScheduler.enable = settings.PROCESS_AUTOMATICALLY
            settings.autoPostProcessorScheduler.start()

            # start the subtitles finder
            settings.subtitlesFinderScheduler.enable = settings.USE_SUBTITLES
            settings.subtitlesFinderScheduler.start()

            # start the trakt checker
            settings.traktCheckerScheduler.enable = settings.USE_TRAKT
            settings.traktCheckerScheduler.start()

            settings.notificationsTaskScheduler.enable = True
            settings.notificationsTaskScheduler.start()
            settings.started["0"] = True


def halt():
    with settings.INIT_LOCK:
        if settings.__INITIALIZED__:
            logger.info("Aborting all threads")

            threads = [
                settings.dailySearchScheduler,
                settings.backlogSearchScheduler,
                settings.showUpdateScheduler,
                settings.versionCheckScheduler,
                settings.showQueueScheduler,
                settings.searchQueueScheduler,
                settings.autoPostProcessorScheduler,
                settings.postProcessorTaskScheduler,
                settings.traktCheckerScheduler,
                settings.properFinderScheduler,
                settings.subtitlesFinderScheduler,
                settings.notificationsTaskScheduler,
                settings.events,
            ]

            # set them all to stop at the same time
            for t in threads:
                t.stop.set()

            for t in threads:
                logger.info(f"Waiting for the {t.name} thread to exit")
                try:
                    t.join(10)
                except Exception:
                    pass

            if settings.ADBA_CONNECTION:
                settings.ADBA_CONNECTION.logout()
                logger.info("Waiting for the ANIDB CONNECTION thread to exit")
                try:
                    settings.ADBA_CONNECTION.join(10)
                except Exception:
                    pass

            settings.__INITIALIZED__.clear()
        settings.started.clear()


def sig_handler(signum=None, frame=None):
    # noinspection PyUnusedLocal
    frame_ = frame
    if not isinstance(signum, type(None)):
        logger.info("Signal {0:d} caught, saving and exiting...".format(int(signum)))
        Shutdown.stop(settings.PID)


def saveAll():
    # write all shows
    logger.info("Saving all shows to the database")
    for show in settings.showList:
        show.saveToDB()

    # save config
    logger.info("Saving config file to disk")
    save_config()


def save_config():
    new_config = ConfigObj(settings.CONFIG_FILE, encoding="UTF-8", indent_type="  ")

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(settings.ITEM_NAME, settings.ENCRYPTION_VERSION)` in save_config()
    # dynamically save provider settings
    for curProvider in providers.sortedProviderList():
        new_config[curProvider.get_id().upper()] = {}
        new_config[curProvider.get_id().upper()][curProvider.get_id()] = int(curProvider.enabled)
        if hasattr(curProvider, "custom_url"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_custom_url")] = curProvider.custom_url
        if hasattr(curProvider, "digest"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_digest")] = curProvider.digest
        if hasattr(curProvider, "hash"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_hash")] = curProvider.hash
        if hasattr(curProvider, "api_key"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_api_key")] = curProvider.api_key
        if hasattr(curProvider, "username"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_username")] = curProvider.username
        if hasattr(curProvider, "password"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_password")] = helpers.encrypt(curProvider.password, settings.ENCRYPTION_VERSION)
        if hasattr(curProvider, "passkey"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_passkey")] = curProvider.passkey
        if hasattr(curProvider, "pin"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_pin")] = curProvider.pin
        if hasattr(curProvider, "confirmed"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_confirmed")] = int(curProvider.confirmed)
        if hasattr(curProvider, "ranked"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_ranked")] = int(curProvider.ranked)
        if hasattr(curProvider, "engrelease"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_engrelease")] = int(curProvider.engrelease)
        if hasattr(curProvider, "onlyspasearch"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_onlyspasearch")] = int(curProvider.onlyspasearch)
        if hasattr(curProvider, "sorting"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_sorting")] = curProvider.sorting
        if hasattr(curProvider, "ratio"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_ratio")] = curProvider.ratio
        if hasattr(curProvider, "minseed"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_minseed")] = int(curProvider.minseed)
        if hasattr(curProvider, "minleech"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_minleech")] = int(curProvider.minleech)
        if hasattr(curProvider, "options"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_options")] = curProvider.options
        if hasattr(curProvider, "freeleech"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_freeleech")] = int(curProvider.freeleech)
        if hasattr(curProvider, "search_mode"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_search_mode")] = curProvider.search_mode
        if hasattr(curProvider, "search_fallback"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_search_fallback")] = int(curProvider.search_fallback)
        if hasattr(curProvider, "enable_daily"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_enable_daily")] = int(curProvider.enable_daily and curProvider.can_daily)
        if hasattr(curProvider, "enable_backlog"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_enable_backlog")] = int(curProvider.enable_backlog and curProvider.can_backlog)
        if hasattr(curProvider, "cat"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_cat")] = int(curProvider.cat)
        if hasattr(curProvider, "subtitle"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_subtitle")] = int(curProvider.subtitle)
        if hasattr(curProvider, "cookies"):
            new_config[curProvider.get_id().upper()][curProvider.get_id("_cookies")] = curProvider.cookies

    new_config.update(
        {
            "General": {
                "git_username": settings.GIT_USERNAME,
                "git_token_password": helpers.encrypt(settings.GIT_TOKEN, settings.ENCRYPTION_VERSION),
                "config_version": settings.CONFIG_VERSION,
                "encryption_version": int(settings.ENCRYPTION_VERSION),
                "encryption_secret": settings.ENCRYPTION_SECRET,
                "log_nr": int(settings.LOG_NR),
                "log_size": float(settings.LOG_SIZE),
                "log_dir": settings.LOG_DIR,
                "socket_timeout": settings.SOCKET_TIMEOUT,
                "web_port": settings.WEB_PORT,
                "web_host": settings.WEB_HOST,
                "web_ipv6": int(settings.WEB_IPV6),
                "web_log": int(settings.WEB_LOG),
                "web_root": settings.WEB_ROOT,
                "web_username": settings.WEB_USERNAME,
                "web_password": helpers.encrypt(settings.WEB_PASSWORD, settings.ENCRYPTION_VERSION),
                "web_cookie_secret": settings.WEB_COOKIE_SECRET,
                "web_use_gzip": int(settings.WEB_USE_GZIP),
                "ssl_verify": int(settings.SSL_VERIFY),
                "download_url": settings.DOWNLOAD_URL,
                "localhost_ip": settings.LOCALHOST_IP,
                "cpu_preset": settings.CPU_PRESET,
                "anon_redirect": settings.ANON_REDIRECT or "disabled",
                "tvdb_user": settings.TVDB_USER,
                "tvdb_user_key": settings.TVDB_USER_KEY,
                "api_key": settings.API_KEY,
                "debug": int(settings.DEBUG),
                "dbdebug": int(settings.DBDEBUG),
                "default_page": settings.DEFAULT_PAGE,
                "enable_https": int(settings.ENABLE_HTTPS),
                "notify_on_login": int(settings.NOTIFY_ON_LOGIN),
                "https_cert": settings.HTTPS_CERT,
                "https_key": settings.HTTPS_KEY,
                "handle_reverse_proxy": int(settings.HANDLE_REVERSE_PROXY),
                "use_nzbs": int(settings.USE_NZBS),
                "use_torrents": int(settings.USE_TORRENTS),
                "nzb_method": settings.NZB_METHOD,
                "torrent_method": settings.TORRENT_METHOD,
                "usenet_retention": int(settings.USENET_RETENTION),
                "cache_retention": int(settings.CACHE_RETENTION),
                "autopostprocessor_frequency": int(settings.AUTOPOSTPROCESSOR_FREQUENCY),
                "dailysearch_frequency": int(settings.DAILYSEARCH_FREQUENCY),
                "backlog_frequency": int(settings.BACKLOG_FREQUENCY),
                "update_frequency": int(settings.UPDATE_FREQUENCY),
                "showupdate_hour": int(settings.SHOWUPDATE_HOUR),
                "download_propers": int(settings.DOWNLOAD_PROPERS),
                "randomize_providers": int(settings.RANDOMIZE_PROVIDERS),
                "check_propers_interval": settings.CHECK_PROPERS_INTERVAL,
                "allow_high_priority": int(settings.ALLOW_HIGH_PRIORITY),
                "skip_removed_files": int(settings.SKIP_REMOVED_FILES),
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "quality_default": int(settings.QUALITY_DEFAULT),
                "quality_allow_hevc": int(settings.QUALITY_ALLOW_HEVC),
                "status_default": int(settings.STATUS_DEFAULT),
                "status_default_after": int(settings.STATUS_DEFAULT_AFTER),
                "season_folders_default": int(settings.SEASON_FOLDERS_DEFAULT),
                "indexer_default": int(settings.INDEXER_DEFAULT),
                "indexer_timeout": int(settings.INDEXER_TIMEOUT),
                "anime_default": int(settings.ANIME_DEFAULT),
                "scene_default": int(settings.SCENE_DEFAULT),
                "provider_order": " ".join(settings.PROVIDER_ORDER),
                "version_notify": int(settings.VERSION_NOTIFY),
                "auto_update": int(settings.AUTO_UPDATE),
                "notify_on_update": int(settings.NOTIFY_ON_UPDATE),
                "naming_strip_year": int(settings.NAMING_STRIP_YEAR),
                "naming_no_brackets": int(settings.NAMING_NO_BRACKETS),
                "naming_pattern": settings.NAMING_PATTERN,
                "naming_custom_abd": int(settings.NAMING_CUSTOM_ABD),
                "naming_abd_pattern": settings.NAMING_ABD_PATTERN,
                "naming_custom_sports": int(settings.NAMING_CUSTOM_SPORTS),
                "naming_sports_pattern": settings.NAMING_SPORTS_PATTERN,
                "naming_custom_anime": int(settings.NAMING_CUSTOM_ANIME),
                "naming_anime_pattern": settings.NAMING_ANIME_PATTERN,
                "naming_multi_ep": int(settings.NAMING_MULTI_EP),
                "naming_anime_multi_ep": int(settings.NAMING_ANIME_MULTI_EP),
                "naming_anime": int(settings.NAMING_ANIME),
                "indexerDefaultLang": settings.INDEXER_DEFAULT_LANGUAGE,
                "ep_default_deleted_status": int(settings.EP_DEFAULT_DELETED_STATUS),
                "launch_browser": int(settings.LAUNCH_BROWSER),
                "trash_remove_show": int(settings.TRASH_REMOVE_SHOW),
                "trash_rotate_logs": int(settings.TRASH_ROTATE_LOGS),
                "ignore_broken_symlinks": int(settings.IGNORE_BROKEN_SYMLINKS),
                "sort_article": int(settings.SORT_ARTICLE),
                "grammar_articles": settings.GRAMMAR_ARTICLES,
                "proxy_setting": settings.PROXY_SETTING,
                "proxy_indexers": int(settings.PROXY_INDEXERS),
                "use_listview": int(settings.USE_LISTVIEW),
                "metadata_kodi": settings.METADATA_KODI,
                "metadata_mediabrowser": settings.METADATA_MEDIABROWSER,
                "metadata_ps3": settings.METADATA_PS3,
                "metadata_wdtv": settings.METADATA_WDTV,
                "metadata_tivo": settings.METADATA_TIVO,
                "metadata_mede8er": settings.METADATA_MEDE8ER,
                "backlog_days": int(settings.BACKLOG_DAYS),
                "backlog_missing_only": int(settings.BACKLOG_MISSING_ONLY),
                "root_dirs": settings.ROOT_DIRS if settings.ROOT_DIRS else "",
                "tv_download_dir": settings.TV_DOWNLOAD_DIR,
                "keep_processed_dir": int(settings.KEEP_PROCESSED_DIR),
                "process_method": settings.PROCESS_METHOD,
                "processor_follow_symlinks": int(settings.PROCESSOR_FOLLOW_SYMLINKS),
                "del_rar_contents": int(settings.DELRARCONTENTS),
                "move_associated_files": int(settings.MOVE_ASSOCIATED_FILES),
                "delete_non_associated_files": int(settings.DELETE_NON_ASSOCIATED_FILES),
                "sync_files": settings.SYNC_FILES,
                "postpone_if_sync_files": int(settings.POSTPONE_IF_SYNC_FILES),
                "nfo_rename": int(settings.NFO_RENAME),
                "process_automatically": int(settings.PROCESS_AUTOMATICALLY),
                "no_delete": int(settings.NO_DELETE),
                "use_icacls": int(settings.USE_ICACLS),
                "unpack": int(settings.UNPACK),
                "unpack_dir": settings.UNPACK_DIR,
                "unrar_tool": settings.UNRAR_TOOL,
                "unar_tool": settings.UNAR_TOOL,
                "rename_episodes": int(settings.RENAME_EPISODES),
                "airdate_episodes": int(settings.AIRDATE_EPISODES),
                "file_timestamp_timezone": settings.FILE_TIMESTAMP_TIMEZONE,
                "create_missing_show_dirs": int(settings.CREATE_MISSING_SHOW_DIRS),
                "add_shows_wo_dir": int(settings.ADD_SHOWS_WO_DIR),
                "add_shows_with_year": int(settings.ADD_SHOWS_WITH_YEAR),
                "use_free_space_check": int(settings.USE_FREE_SPACE_CHECK),
                "extra_scripts": "|".join(settings.EXTRA_SCRIPTS),
                "ignore_words": settings.IGNORE_WORDS,
                "trackers_list": settings.TRACKERS_LIST,
                "require_words": settings.REQUIRE_WORDS,
                "prefer_words": settings.PREFER_WORDS,
                "ignored_subs_list": settings.IGNORED_SUBS_LIST,
                "calendar_unprotected": int(settings.CALENDAR_UNPROTECTED),
                "calendar_icons": int(settings.CALENDAR_ICONS),
                "no_restart": int(settings.NO_RESTART),
                "developer": int(settings.DEVELOPER),
                "display_all_seasons": int(settings.DISPLAY_ALL_SEASONS),
                "ended_shows_update_interval": int(settings.ENDED_SHOWS_UPDATE_INTERVAL),
                "news_last_read": settings.NEWS_LAST_READ,
                "flaresolverr_uri": settings.FLARESOLVERR_URI,
            },
            "Cloudflare": {"auth_domain": settings.CF_AUTH_DOMAIN, "audience_policy": settings.CF_POLICY_AUD},
            "Shares": settings.WINDOWS_SHARES,
            "Blackhole": {
                "nzb_dir": settings.NZB_DIR,
                "torrent_dir": settings.TORRENT_DIR,
            },
            "NZBs": {
                "nzbs": int(settings.NZBS),
                "nzbs_uid": settings.NZBS_UID,
                "nzbs_hash": settings.NZBS_HASH,
            },
            "Newzbin": {
                "newzbin": int(settings.NEWZBIN),
                "newzbin_username": settings.NEWZBIN_USERNAME,
                "newzbin_password": helpers.encrypt(settings.NEWZBIN_PASSWORD, settings.ENCRYPTION_VERSION),
            },
            "SABnzbd": {
                "sab_username": settings.SAB_USERNAME,
                "sab_password": helpers.encrypt(settings.SAB_PASSWORD, settings.ENCRYPTION_VERSION),
                "sab_apikey": settings.SAB_APIKEY,
                "sab_category": settings.SAB_CATEGORY,
                "sab_category_backlog": settings.SAB_CATEGORY_BACKLOG,
                "sab_category_anime": settings.SAB_CATEGORY_ANIME,
                "sab_category_anime_backlog": settings.SAB_CATEGORY_ANIME_BACKLOG,
                "sab_host": settings.SAB_HOST,
                "sab_forced": int(settings.SAB_FORCED),
            },
            "NZBget": {
                "nzbget_username": settings.NZBGET_USERNAME,
                "nzbget_password": helpers.encrypt(settings.NZBGET_PASSWORD, settings.ENCRYPTION_VERSION),
                "nzbget_category": settings.NZBGET_CATEGORY,
                "nzbget_category_backlog": settings.NZBGET_CATEGORY_BACKLOG,
                "nzbget_category_anime": settings.NZBGET_CATEGORY_ANIME,
                "nzbget_category_anime_backlog": settings.NZBGET_CATEGORY_ANIME_BACKLOG,
                "nzbget_host": settings.NZBGET_HOST,
                "nzbget_use_https": int(settings.NZBGET_USE_HTTPS),
                "nzbget_priority": settings.NZBGET_PRIORITY,
            },
            "TORRENT": {
                "torrent_username": settings.TORRENT_USERNAME,
                "torrent_password": helpers.encrypt(settings.TORRENT_PASSWORD, settings.ENCRYPTION_VERSION),
                "torrent_host": settings.TORRENT_HOST,
                "torrent_path": settings.TORRENT_PATH,
                "torrent_path_incomplete": settings.TORRENT_PATH_INCOMPLETE,
                "torrent_seed_time": int(settings.TORRENT_SEED_TIME),
                "torrent_paused": int(settings.TORRENT_PAUSED),
                "torrent_high_bandwidth": int(settings.TORRENT_HIGH_BANDWIDTH),
                "torrent_label": settings.TORRENT_LABEL,
                "torrent_label_anime": settings.TORRENT_LABEL_ANIME,
                "torrent_verify_cert": int(settings.TORRENT_VERIFY_CERT),
                "torrent_rpcurl": settings.TORRENT_RPCURL,
                "torrent_auth_type": settings.TORRENT_AUTH_TYPE,
            },
            "KODI": {
                "use_kodi": int(settings.USE_KODI),
                "kodi_always_on": int(settings.KODI_ALWAYS_ON),
                "kodi_notify_onsnatch": int(settings.KODI_NOTIFY_ONSNATCH),
                "kodi_notify_ondownload": int(settings.KODI_NOTIFY_ONDOWNLOAD),
                "kodi_notify_onsubtitledownload": int(settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD),
                "kodi_update_library": int(settings.KODI_UPDATE_LIBRARY),
                "kodi_update_full": int(settings.KODI_UPDATE_FULL),
                "kodi_update_onlyfirst": int(settings.KODI_UPDATE_ONLYFIRST),
                "kodi_host": settings.KODI_HOST,
                "kodi_username": settings.KODI_USERNAME,
                "kodi_password": helpers.encrypt(settings.KODI_PASSWORD, settings.ENCRYPTION_VERSION),
            },
            "Plex": {
                "use_plex_server": int(settings.USE_PLEX_SERVER),
                "plex_notify_onsnatch": int(settings.PLEX_NOTIFY_ONSNATCH),
                "plex_notify_ondownload": int(settings.PLEX_NOTIFY_ONDOWNLOAD),
                "plex_notify_onsubtitledownload": int(settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD),
                "plex_update_library": int(settings.PLEX_UPDATE_LIBRARY),
                "plex_server_host": settings.PLEX_SERVER_HOST,
                "plex_server_token": settings.PLEX_SERVER_TOKEN,
                "plex_client_host": settings.PLEX_CLIENT_HOST,
                "plex_server_username": settings.PLEX_SERVER_USERNAME,
                "plex_server_password": helpers.encrypt(settings.PLEX_SERVER_PASSWORD, settings.ENCRYPTION_VERSION),
                "use_plex_client": int(settings.USE_PLEX_CLIENT),
                "plex_client_username": settings.PLEX_CLIENT_USERNAME,
                "plex_client_password": helpers.encrypt(settings.PLEX_CLIENT_PASSWORD, settings.ENCRYPTION_VERSION),
                "plex_server_https": int(settings.PLEX_SERVER_HTTPS),
            },
            "Emby": {
                "use_emby": int(settings.USE_EMBY),
                "emby_host": settings.EMBY_HOST,
                "emby_apikey": settings.EMBY_APIKEY,
            },
            "Growl": {
                "use_growl": int(settings.USE_GROWL),
                "growl_notify_onsnatch": int(settings.GROWL_NOTIFY_ONSNATCH),
                "growl_notify_ondownload": int(settings.GROWL_NOTIFY_ONDOWNLOAD),
                "growl_notify_onsubtitledownload": int(settings.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
                "growl_host": settings.GROWL_HOST,
                "growl_password": helpers.encrypt(settings.GROWL_PASSWORD, settings.ENCRYPTION_VERSION),
            },
            "FreeMobile": {
                "use_freemobile": int(settings.USE_FREEMOBILE),
                "freemobile_notify_onsnatch": int(settings.FREEMOBILE_NOTIFY_ONSNATCH),
                "freemobile_notify_ondownload": int(settings.FREEMOBILE_NOTIFY_ONDOWNLOAD),
                "freemobile_notify_onsubtitledownload": int(settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD),
                "freemobile_id": settings.FREEMOBILE_ID,
                "freemobile_apikey": settings.FREEMOBILE_APIKEY,
            },
            "Telegram": {
                "use_telegram": int(settings.USE_TELEGRAM),
                "telegram_notify_onsnatch": int(settings.TELEGRAM_NOTIFY_ONSNATCH),
                "telegram_notify_ondownload": int(settings.TELEGRAM_NOTIFY_ONDOWNLOAD),
                "telegram_notify_onsubtitledownload": int(settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD),
                "telegram_id": settings.TELEGRAM_ID,
                "telegram_apikey": settings.TELEGRAM_APIKEY,
            },
            "Join": {
                "use_join": int(settings.USE_JOIN),
                "join_notify_onsnatch": int(settings.JOIN_NOTIFY_ONSNATCH),
                "join_notify_ondownload": int(settings.JOIN_NOTIFY_ONDOWNLOAD),
                "join_notify_onsubtitledownload": int(settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD),
                "join_id": settings.JOIN_ID,
                "join_apikey": settings.JOIN_APIKEY,
            },
            "Prowl": {
                "use_prowl": int(settings.USE_PROWL),
                "prowl_notify_onsnatch": int(settings.PROWL_NOTIFY_ONSNATCH),
                "prowl_notify_ondownload": int(settings.PROWL_NOTIFY_ONDOWNLOAD),
                "prowl_notify_onsubtitledownload": int(settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
                "prowl_api": settings.PROWL_API,
                "prowl_priority": settings.PROWL_PRIORITY,
                "prowl_message_title": settings.PROWL_MESSAGE_TITLE,
            },
            "Twitter": {
                "use_twitter": int(settings.USE_TWITTER),
                "twitter_notify_onsnatch": int(settings.TWITTER_NOTIFY_ONSNATCH),
                "twitter_notify_ondownload": int(settings.TWITTER_NOTIFY_ONDOWNLOAD),
                "twitter_notify_onsubtitledownload": int(settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD),
                "twitter_username": settings.TWITTER_USERNAME,
                "twitter_password": helpers.encrypt(settings.TWITTER_PASSWORD, settings.ENCRYPTION_VERSION),
                "twitter_prefix": settings.TWITTER_PREFIX,
                "twitter_dmto": settings.TWITTER_DMTO,
                "twitter_usedm": int(settings.TWITTER_USEDM),
            },
            "Twilio": {
                "use_twilio": int(settings.USE_TWILIO),
                "twilio_notify_onsnatch": int(settings.TWILIO_NOTIFY_ONSNATCH),
                "twilio_notify_ondownload": int(settings.TWILIO_NOTIFY_ONDOWNLOAD),
                "twilio_notify_onsubtitledownload": int(settings.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD),
                "twilio_phone_sid": helpers.encrypt(settings.TWILIO_PHONE_SID, settings.ENCRYPTION_VERSION),
                "twilio_account_sid": helpers.encrypt(settings.TWILIO_ACCOUNT_SID, settings.ENCRYPTION_VERSION),
                "twilio_auth_token": helpers.encrypt(settings.TWILIO_AUTH_TOKEN, settings.ENCRYPTION_VERSION),
                "twilio_to_number": helpers.encrypt(settings.TWILIO_TO_NUMBER, settings.ENCRYPTION_VERSION),
            },
            "Boxcar2": {
                "use_boxcar2": int(settings.USE_BOXCAR2),
                "boxcar2_notify_onsnatch": int(settings.BOXCAR2_NOTIFY_ONSNATCH),
                "boxcar2_notify_ondownload": int(settings.BOXCAR2_NOTIFY_ONDOWNLOAD),
                "boxcar2_notify_onsubtitledownload": int(settings.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD),
                "boxcar2_accesstoken": settings.BOXCAR2_ACCESSTOKEN,
            },
            "Pushover": {
                "use_pushover": int(settings.USE_PUSHOVER),
                "pushover_notify_onsnatch": int(settings.PUSHOVER_NOTIFY_ONSNATCH),
                "pushover_notify_ondownload": int(settings.PUSHOVER_NOTIFY_ONDOWNLOAD),
                "pushover_notify_onsubtitledownload": int(settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD),
                "pushover_userkey": settings.PUSHOVER_USERKEY,
                "pushover_apikey": settings.PUSHOVER_APIKEY,
                "pushover_device": settings.PUSHOVER_DEVICE,
                "pushover_sound": settings.PUSHOVER_SOUND,
                "pushover_priority": settings.PUSHOVER_PRIORITY,
            },
            "Libnotify": {
                "use_libnotify": int(settings.USE_LIBNOTIFY),
                "libnotify_notify_onsnatch": int(settings.LIBNOTIFY_NOTIFY_ONSNATCH),
                "libnotify_notify_ondownload": int(settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD),
                "libnotify_notify_onsubtitledownload": int(settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD),
            },
            "NMJ": {"use_nmj": int(settings.USE_NMJ), "nmj_host": settings.NMJ_HOST, "nmj_database": settings.NMJ_DATABASE, "nmj_mount": settings.NMJ_MOUNT},
            "NMJv2": {
                "use_nmjv2": int(settings.USE_NMJv2),
                "nmjv2_host": settings.NMJv2_HOST,
                "nmjv2_database": settings.NMJv2_DATABASE,
                "nmjv2_dbloc": settings.NMJv2_DBLOC,
            },
            "Synology": {
                "use_synoindex": int(settings.USE_SYNOINDEX),
                "host": settings.SYNOLOGY_DSM_HOST,
                "username": settings.SYNOLOGY_DSM_USERNAME,
                "password": helpers.encrypt(settings.SYNOLOGY_DSM_PASSWORD, settings.ENCRYPTION_VERSION),
                "path": settings.SYNOLOGY_DSM_PATH,
            },
            "SynologyNotifier": {
                "use_synologynotifier": int(settings.USE_SYNOLOGYNOTIFIER),
                "synologynotifier_notify_onsnatch": int(settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH),
                "synologynotifier_notify_ondownload": int(settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD),
                "synologynotifier_notify_onsubtitledownload": int(settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD),
            },
            "Slack": {
                "use_slack": int(settings.USE_SLACK),
                "slack_notify_snatch": int(settings.SLACK_NOTIFY_SNATCH),
                "slack_notify_download": int(settings.SLACK_NOTIFY_DOWNLOAD),
                "slack_notify_subtitledownload": int(settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD),
                "slack_webhook": settings.SLACK_WEBHOOK,
                "slack_icon_emoji": settings.SLACK_ICON_EMOJI,
            },
            "RocketChat": {
                "use_rocketchat": int(settings.USE_ROCKETCHAT),
                "rocketchat_notify_snatch": int(settings.ROCKETCHAT_NOTIFY_SNATCH),
                "rocketchat_notify_download": int(settings.ROCKETCHAT_NOTIFY_DOWNLOAD),
                "rocketchat_notify_subtitledownload": int(settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD),
                "rocketchat_webhook": settings.ROCKETCHAT_WEBHOOK,
                "rocketchat_icon_emoji": settings.ROCKETCHAT_ICON_EMOJI,
            },
            "Matrix": {
                "use_matrix": int(settings.USE_MATRIX),
                "matrix_notify_snatch": int(settings.MATRIX_NOTIFY_SNATCH),
                "matrix_notify_download": int(settings.MATRIX_NOTIFY_DOWNLOAD),
                "matrix_notify_subtitledownload": int(settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD),
                "matrix_api_token": settings.MATRIX_API_TOKEN,
                "matrix_server": settings.MATRIX_SERVER,
                "matrix_room": settings.MATRIX_ROOM,
            },
            "Discord": {
                "use_discord": int(settings.USE_DISCORD),
                "discord_notify_snatch": int(settings.DISCORD_NOTIFY_SNATCH),
                "discord_notify_download": int(settings.DISCORD_NOTIFY_DOWNLOAD),
                "discord_webhook": settings.DISCORD_WEBHOOK,
                "discord_name": settings.DISCORD_NAME,
                "discord_avatar_url": settings.DISCORD_AVATAR_URL,
                "discord_tts": settings.DISCORD_TTS,
            },
            "Trakt": {
                "use_trakt": int(settings.USE_TRAKT),
                "trakt_username": settings.TRAKT_USERNAME,
                "trakt_access_token": settings.TRAKT_ACCESS_TOKEN,
                "trakt_refresh_token": settings.TRAKT_REFRESH_TOKEN,
                "trakt_remove_watchlist": int(settings.TRAKT_REMOVE_WATCHLIST),
                "trakt_remove_serieslist": int(settings.TRAKT_REMOVE_SERIESLIST),
                "trakt_remove_show_from_sickchill": int(settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL),
                "trakt_sync_watchlist": int(settings.TRAKT_SYNC_WATCHLIST),
                "trakt_method_add": int(settings.TRAKT_METHOD_ADD),
                "trakt_start_paused": int(settings.TRAKT_START_PAUSED),
                "trakt_use_recommended": int(settings.TRAKT_USE_RECOMMENDED),
                "trakt_sync": int(settings.TRAKT_SYNC),
                "trakt_sync_remove": int(settings.TRAKT_SYNC_REMOVE),
                "trakt_default_indexer": int(settings.TRAKT_DEFAULT_INDEXER),
                "trakt_timeout": int(settings.TRAKT_TIMEOUT),
                "trakt_blacklist_name": settings.TRAKT_BLACKLIST_NAME,
            },
            "pyTivo": {
                "use_pytivo": int(settings.USE_PYTIVO),
                "pytivo_notify_onsnatch": int(settings.PYTIVO_NOTIFY_ONSNATCH),
                "pytivo_notify_ondownload": int(settings.PYTIVO_NOTIFY_ONDOWNLOAD),
                "pytivo_notify_onsubtitledownload": int(settings.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD),
                "pyTivo_update_library": int(settings.PYTIVO_UPDATE_LIBRARY),
                "pytivo_host": settings.PYTIVO_HOST,
                "pytivo_share_name": settings.PYTIVO_SHARE_NAME,
                "pytivo_tivo_name": settings.PYTIVO_TIVO_NAME,
            },
            "NMA": {
                "use_nma": int(settings.USE_NMA),
                "nma_notify_onsnatch": int(settings.NMA_NOTIFY_ONSNATCH),
                "nma_notify_ondownload": int(settings.NMA_NOTIFY_ONDOWNLOAD),
                "nma_notify_onsubtitledownload": int(settings.NMA_NOTIFY_ONSUBTITLEDOWNLOAD),
                "nma_api": settings.NMA_API,
                "nma_priority": settings.NMA_PRIORITY,
            },
            "Pushalot": {
                "use_pushalot": int(settings.USE_PUSHALOT),
                "pushalot_notify_onsnatch": int(settings.PUSHALOT_NOTIFY_ONSNATCH),
                "pushalot_notify_ondownload": int(settings.PUSHALOT_NOTIFY_ONDOWNLOAD),
                "pushalot_notify_onsubtitledownload": int(settings.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD),
                "pushalot_authorizationtoken": settings.PUSHALOT_AUTHORIZATIONTOKEN,
            },
            "Pushbullet": {
                "use_pushbullet": int(settings.USE_PUSHBULLET),
                "pushbullet_notify_onsnatch": int(settings.PUSHBULLET_NOTIFY_ONSNATCH),
                "pushbullet_notify_ondownload": int(settings.PUSHBULLET_NOTIFY_ONDOWNLOAD),
                "pushbullet_notify_onsubtitledownload": int(settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD),
                "pushbullet_api": settings.PUSHBULLET_API,
                "pushbullet_device": settings.PUSHBULLET_DEVICE,
                "pushbullet_channel": settings.PUSHBULLET_CHANNEL,
            },
            "Email": {
                "use_email": int(settings.USE_EMAIL),
                "email_notify_onsnatch": int(settings.EMAIL_NOTIFY_ONSNATCH),
                "email_notify_ondownload": int(settings.EMAIL_NOTIFY_ONDOWNLOAD),
                "email_notify_onpostprocess": int(settings.EMAIL_NOTIFY_ONPOSTPROCESS),
                "email_notify_onsubtitledownload": int(settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD),
                "email_host": settings.EMAIL_HOST,
                "email_port": int(settings.EMAIL_PORT),
                "email_tls": int(settings.EMAIL_TLS),
                "email_user": settings.EMAIL_USER,
                "email_password": helpers.encrypt(settings.EMAIL_PASSWORD, settings.ENCRYPTION_VERSION),
                "email_from": settings.EMAIL_FROM,
                "email_list": settings.EMAIL_LIST,
                "email_subject": settings.EMAIL_SUBJECT,
            },
            "Newznab": {"newznab_data": settings.NEWZNAB_DATA},
            "TorrentRss": {"torrentrss_data": "!!!".join([x.configStr() for x in settings.torrentRssProviderList])},
            "GUI": {
                "gui_name": settings.GUI_NAME,
                "language": settings.GUI_LANG,
                "theme_name": settings.THEME_NAME,
                "sickchill_background": int(settings.SICKCHILL_BACKGROUND),
                "sickchill_background_path": settings.SICKCHILL_BACKGROUND_PATH,
                "fanart_background": int(settings.FANART_BACKGROUND),
                "fanart_background_opacity": settings.FANART_BACKGROUND_OPACITY,
                "custom_css": int(settings.CUSTOM_CSS),
                "custom_css_path": settings.CUSTOM_CSS_PATH,
                "home_layout": settings.HOME_LAYOUT,
                "history_layout": settings.HISTORY_LAYOUT,
                "history_limit": settings.HISTORY_LIMIT,
                "display_show_specials": int(settings.DISPLAY_SHOW_SPECIALS),
                "coming_eps_layout": settings.COMING_EPS_LAYOUT,
                "coming_eps_display_paused": int(settings.COMING_EPS_DISPLAY_PAUSED),
                "coming_eps_display_snatched": int(settings.COMING_EPS_DISPLAY_SNATCHED),
                "coming_eps_sort": settings.COMING_EPS_SORT,
                "coming_eps_missed_range": config.min_max(settings.COMING_EPS_MISSED_RANGE, 7, 0, 42810),
                "fuzzy_dating": int(settings.FUZZY_DATING),
                "trim_zero": int(settings.TRIM_ZERO),
                "date_preset": settings.DATE_PRESET,
                "time_preset": settings.TIME_PRESET_W_SECONDS,
                "timezone_display": settings.TIMEZONE_DISPLAY,
                "poster_sortby": settings.POSTER_SORTBY,
                "poster_sortdir": settings.POSTER_SORTDIR,
                "no_lgmargin": int(settings.NO_LGMARGIN),
            },
            "Subtitles": {
                "use_subtitles": int(settings.USE_SUBTITLES),
                "subtitles_include_specials": int(settings.SUBTITLES_INCLUDE_SPECIALS),
                "subtitles_languages": ",".join(settings.SUBTITLES_LANGUAGES),
                "SUBTITLES_SERVICES_LIST": ",".join(settings.SUBTITLES_SERVICES_LIST),
                "SUBTITLES_SERVICES_ENABLED": "|".join([str(x) for x in settings.SUBTITLES_SERVICES_ENABLED]),
                "subtitles_dir": settings.SUBTITLES_DIR,
                "subtitles_default": int(settings.SUBTITLES_DEFAULT),
                "subtitles_history": int(settings.SUBTITLES_HISTORY),
                "subtitles_perfect_match": int(settings.SUBTITLES_PERFECT_MATCH),
                "embedded_subtitles_all": int(settings.EMBEDDED_SUBTITLES_ALL),
                "subtitles_hearing_impaired": int(settings.SUBTITLES_HEARING_IMPAIRED),
                "subtitles_finder_frequency": int(settings.SUBTITLES_FINDER_FREQUENCY),
                "subtitles_multi": int(settings.SUBTITLES_MULTI),
                "subtitles_extra_scripts": "|".join(settings.SUBTITLES_EXTRA_SCRIPTS),
                "subtitles_keep_only_wanted": int(settings.SUBTITLES_KEEP_ONLY_WANTED),
                "addic7ed_username": settings.ADDIC7ED_USER,
                "addic7ed_password": helpers.encrypt(settings.ADDIC7ED_PASS, settings.ENCRYPTION_VERSION),
                "itasa_username": settings.ITASA_USER,
                "itasa_password": helpers.encrypt(settings.ITASA_PASS, settings.ENCRYPTION_VERSION),
                "legendastv_username": settings.LEGENDASTV_USER,
                "legendastv_password": helpers.encrypt(settings.LEGENDASTV_PASS, settings.ENCRYPTION_VERSION),
                "opensubtitles_username": settings.OPENSUBTITLES_USER,
                "opensubtitles_password": helpers.encrypt(settings.OPENSUBTITLES_PASS, settings.ENCRYPTION_VERSION),
                "subscenter_username": settings.SUBSCENTER_USER,
                "subscenter_password": helpers.encrypt(settings.SUBSCENTER_PASS, settings.ENCRYPTION_VERSION),
            },
            "FailedDownloads": {
                "use_failed_downloads": int(settings.USE_FAILED_DOWNLOADS),
                "delete_failed": int(settings.DELETE_FAILED),
            },
            "ANIDB": {
                "use_anidb": int(settings.USE_ANIDB),
                "anidb_username": settings.ANIDB_USERNAME,
                "anidb_password": helpers.encrypt(settings.ANIDB_PASSWORD, settings.ENCRYPTION_VERSION),
                "anidb_use_mylist": int(settings.ANIDB_USE_MYLIST),
            },
            "ANIME": {
                "anime_split_home": int(settings.ANIME_SPLIT_HOME),
                "anime_split_home_in_tabs": int(settings.ANIME_SPLIT_HOME_IN_TABS),
            },
        }
    )
    new_config.write()


def launchBrowser(protocol="http", startPort=None, web_root="/"):

    try:
        import webbrowser
    except ImportError:
        logger.warning("Unable to load the webbrowser module, cannot launch the browser.")
        return

    if not startPort:
        startPort = settings.WEB_PORT

    browserURL = f"{protocol}://localhost:{startPort:d}{web_root}/home/"

    try:
        webbrowser.open(browserURL, 2, True)
    except Exception:
        try:
            webbrowser.open(browserURL, 1, True)
        except Exception:
            logger.exception("Unable to launch a browser")
