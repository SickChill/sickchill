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
from sickchill.init_helpers import locale_dir, setup_gettext
from sickchill.oldbeard import (
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
from sickchill.oldbeard.common import ARCHIVED, IGNORED, MULTI_EP_STRINGS, SD, SKIPPED, WANTED
from sickchill.oldbeard.config import (
    ConfigMigrator,
    check_section,
    check_setting_bool,
    check_setting_float,
    check_setting_int,
    check_setting_str,
    peek_setting_bool,
    peek_setting_int,
    peek_setting_str,
)
from sickchill.oldbeard.databases import cache, failed, main
from sickchill.oldbeard.network_timezones import sc_now
from sickchill.oldbeard.providers.newznab import NewznabProvider
from sickchill.oldbeard.providers.rsstorrent import TorrentRssProvider
from sickchill.system.Shutdown import Shutdown


def initialize(console_logging: bool = True, debug: bool = False, dbdebug: bool = False, disable_file_logging: bool = False) -> bool:
    with settings.INIT_LOCK:
        if settings.__INITIALIZED__:
            return False

        check_section(settings.CFG, "General")
        # Migrated notifiers/clients/metadata/providers live under [NOTIFIERS]/[CLIENTS]/[METADATA]/[PROVIDERS].
        # Do not recreate empty legacy KODI/Plex/.../SABnzbd/Blackhole/Synology/ABNORMAL sections.
        check_section(settings.CFG, "Newzbin")
        check_section(settings.CFG, "Subtitles")

        # Need to be before any passwords
        settings.ENCRYPTION_VERSION = check_setting_int(settings.CFG, "General", "encryption_version", min_val=0, max_val=2)
        settings.ENCRYPTION_SECRET = check_setting_str(settings.CFG, "General", "encryption_secret", helpers.generateCookieSecret(), censor_log=True)

        # git login info
        settings.DEVELOPER = check_setting_bool(settings.CFG, "General", "developer")

        # debugging
        settings.DEBUG = check_setting_bool(settings.CFG, "General", "debug") or debug
        settings.DBDEBUG = check_setting_bool(settings.CFG, "General", "dbdebug") or dbdebug

        settings.DEFAULT_PAGE = check_setting_str(settings.CFG, "General", "default_page", "home")
        if settings.DEFAULT_PAGE not in ("home", "schedule", "history", "news"):
            settings.DEFAULT_PAGE = "home"

        settings.LOG_DIR = check_setting_str(settings.CFG, "General", "log_dir", os.path.normpath(os.path.join(settings.DATA_DIR, "Logs")))
        settings.LOG_NR = check_setting_int(settings.CFG, "General", "log_nr", 5, min_val=1)  # Default to 5 backup file (sickchill.log.x)
        settings.LOG_SIZE = check_setting_float(settings.CFG, "General", "log_size", 10.0, min_val=0.5)  # Default to max 10MB per logfile

        if settings.LOG_SIZE > 100:
            settings.LOG_SIZE = 10.0
        file_logging = not disable_file_logging

        if file_logging and not (helpers.makeDir(settings.LOG_DIR) and os.access(settings.LOG_DIR, os.W_OK)):
            sys.stderr.write("!!! No log folder or log folder not writable, logging to console only!\n")
            file_logging = False

        # init logging
        logger.init_logging(console_logging=console_logging, file_logging=file_logging, debug_logging=settings.DEBUG, database_logging=settings.DBDEBUG)

        settings.GUI_NAME = check_setting_str(settings.CFG, "GUI", "gui_name", "slick")
        settings.GUI_LANG = check_setting_str(settings.CFG, "GUI", "language")

        setup_gettext(settings.GUI_LANG)

        load_gettext_translations(locale_dir, "messages")

        settings.CACHE_DIR = os.path.normpath(os.path.join(settings.DATA_DIR, "cache"))

        # Check if we need to perform a restore of the cache folder
        try:
            restore_dir = os.path.join(settings.DATA_DIR, "restore")
            if os.path.exists(restore_dir) and os.path.exists(os.path.join(restore_dir, "cache")):

                def restore_cache(source, destination):
                    def path_leaf(path):
                        head, tail = os.path.split(path)
                        return tail or os.path.basename(head)

                    try:
                        if os.path.isdir(destination):
                            backup_name = "{0}-{1}".format(path_leaf(destination), datetime.datetime.strftime(sc_now(), "%Y%m%d_%H%M%S"))
                            shutil.move(destination, os.path.join(os.path.dirname(destination), backup_name))

                        shutil.move(source, destination)
                        logger.info("Restore: restoring cache successful")
                    except Exception as er:
                        logger.exception(f"Restore: restoring cache failed: {er}")

                restore_cache(os.path.join(restore_dir, "cache"), settings.CACHE_DIR)
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
        if settings.ANON_REDIRECT in ("http://dereferer.org/?", "https://anonym.to/?"):
            settings.ANON_REDIRECT = settings.DEFAULT_ANON_REDIRECT

        settings.PROXY_SETTING = check_setting_str(settings.CFG, "General", "proxy_setting")
        if settings.PROXY_SETTING:
            settings.PROXY_SETTING = config.clean_url(settings.PROXY_SETTING).rstrip("/")

        settings.PROXY_INDEXERS = check_setting_bool(settings.CFG, "General", "proxy_indexers", True)

        settings.INDEXER_DEFAULT_LANGUAGE = check_setting_str(settings.CFG, "General", "indexerDefaultLang", "en")
        settings.INDEXER_DEFAULT = check_setting_int(settings.CFG, "General", "indexer_default", min_val=1, max_val=2, def_val=1)
        settings.INDEXER_TIMEOUT = check_setting_int(settings.CFG, "General", "indexer_timeout", 20, min_val=0)

        sickchill.indexer = sickchill.ShowIndexer()

        # TheTVDB v4 API key:
        #   1) env TVDB_V4_APIKEY if set, 2) from config.ini, 3) else built-in project key
        settings.TVDB_V4_APIKEY = os.environ.get("TVDB_V4_APIKEY") or check_setting_str(
            settings.CFG,
            "General",
            "tvdb_v4_apikey",
            settings.TVDB_V4_APIKEY_BUILTIN,
            censor_log=True,
        )
        if not (settings.TVDB_V4_APIKEY or "").strip():
            settings.TVDB_V4_APIKEY = settings.TVDB_V4_APIKEY_BUILTIN
            settings.CFG.setdefault("General", {})["tvdb_v4_apikey"] = settings.TVDB_V4_APIKEY_BUILTIN
        # PIN is not named "*password*", so decrypt explicitly (legacy plaintext migrates on save).
        raw_tvdb_pin = os.environ.get("TVDB_V4_PIN") or check_setting_str(settings.CFG, "General", "tvdb_v4_pin", "", censor_log=True)
        settings.TVDB_V4_PIN = helpers.decrypt_config_value(raw_tvdb_pin) or None
        if not (settings.TVDB_V4_PIN or "").strip():
            settings.TVDB_V4_PIN = None
        # Env values skip check_setting_str's censor_log path — always register final credentials.
        if settings.TVDB_V4_APIKEY:
            logger.censored_items[("General", "tvdb_v4_apikey")] = settings.TVDB_V4_APIKEY
        if settings.TVDB_V4_PIN:
            logger.censored_items[("General", "tvdb_v4_pin")] = settings.TVDB_V4_PIN

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

        settings.WHITELIST_DEFAULT = check_setting_str(settings.CFG, "General", "whitelist_default").split(",")
        settings.BLACKLIST_DEFAULT = check_setting_str(settings.CFG, "General", "blacklist_default").split(",")

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
        settings.DOWNLOAD_PROPERS_WINDOW_DAYS = check_setting_int(settings.CFG, "General", "download_propers_window_days", 2, min_val=1, max_val=7)
        settings.CHECK_PROPERS_INTERVAL = check_setting_str(settings.CFG, "General", "check_propers_interval")
        # Legacy UI values: 15m→30m, 45m→90m (persist so config.ini is updated)
        _legacy_propers = {"15m": "30m", "45m": "90m"}
        if settings.CHECK_PROPERS_INTERVAL in _legacy_propers:
            settings.CHECK_PROPERS_INTERVAL = _legacy_propers[settings.CHECK_PROPERS_INTERVAL]
            settings.CFG.setdefault("General", {})["check_propers_interval"] = settings.CHECK_PROPERS_INTERVAL
            settings.CFG.write()
        if settings.CHECK_PROPERS_INTERVAL not in ("30m", "90m", "4h", "8h", "daily"):
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

        # Prefer [CLIENTS] when present so check_setting_* does not recreate empty legacy sections.
        _clients = settings.CFG.get("CLIENTS") if settings.CFG is not None else None

        _bh_client = _clients.get("blackhole") if isinstance(_clients, dict) else None
        if isinstance(_bh_client, dict) and ("nzb_dir" in _bh_client or "torrent_dir" in _bh_client):
            settings.NZB_DIR = _bh_client.get("nzb_dir") or ""
            settings.TORRENT_DIR = _bh_client.get("torrent_dir") or ""
        else:
            settings.NZB_DIR = peek_setting_str(settings.CFG, "Blackhole", "nzb_dir")
            settings.TORRENT_DIR = peek_setting_str(settings.CFG, "Blackhole", "torrent_dir")

        _sab_client = _clients.get("sabnzbd") if isinstance(_clients, dict) else None
        if isinstance(_sab_client, dict) and (_sab_client.get("host") or _sab_client.get("apikey") or _sab_client.get("username") or "category" in _sab_client):
            settings.SAB_USERNAME = _sab_client.get("username") or ""
            settings.SAB_PASSWORD = _sab_client.get("password") or ""
            settings.SAB_APIKEY = _sab_client.get("apikey") or ""
            settings.SAB_CATEGORY = _sab_client.get("category") or "tv"
            settings.SAB_CATEGORY_BACKLOG = _sab_client.get("category_backlog") or settings.SAB_CATEGORY
            settings.SAB_CATEGORY_ANIME = _sab_client.get("category_anime") or "anime"
            settings.SAB_CATEGORY_ANIME_BACKLOG = _sab_client.get("category_anime_backlog") or settings.SAB_CATEGORY_ANIME
            settings.SAB_HOST = _sab_client.get("host") or ""
            settings.SAB_FORCED = str(_sab_client.get("forced", "")).lower() in {"1", "true", "yes", "on"}
            if settings.SAB_PASSWORD:
                logger.censored_items[("CLIENTS", "sabnzbd.password")] = settings.SAB_PASSWORD
            if settings.SAB_APIKEY:
                logger.censored_items[("CLIENTS", "sabnzbd.apikey")] = settings.SAB_APIKEY
        else:
            settings.SAB_USERNAME = peek_setting_str(settings.CFG, "SABnzbd", "sab_username", censor_log=True)
            settings.SAB_PASSWORD = peek_setting_str(settings.CFG, "SABnzbd", "sab_password", censor_log=True)
            settings.SAB_APIKEY = peek_setting_str(settings.CFG, "SABnzbd", "sab_apikey", censor_log=True)
            settings.SAB_CATEGORY = peek_setting_str(settings.CFG, "SABnzbd", "sab_category", "tv")
            settings.SAB_CATEGORY_BACKLOG = peek_setting_str(settings.CFG, "SABnzbd", "sab_category_backlog", settings.SAB_CATEGORY)
            settings.SAB_CATEGORY_ANIME = peek_setting_str(settings.CFG, "SABnzbd", "sab_category_anime", "anime")
            settings.SAB_CATEGORY_ANIME_BACKLOG = peek_setting_str(settings.CFG, "SABnzbd", "sab_category_anime_backlog", settings.SAB_CATEGORY_ANIME)
            settings.SAB_HOST = peek_setting_str(settings.CFG, "SABnzbd", "sab_host")
            settings.SAB_FORCED = peek_setting_bool(settings.CFG, "SABnzbd", "sab_forced")

        _nzbget_client = _clients.get("nzbget") if isinstance(_clients, dict) else None
        if isinstance(_nzbget_client, dict) and (_nzbget_client.get("host") or _nzbget_client.get("username") or "category" in _nzbget_client):
            settings.NZBGET_USERNAME = _nzbget_client.get("username") or "nzbget"
            settings.NZBGET_PASSWORD = _nzbget_client.get("password") or "tegbzn6789"
            settings.NZBGET_CATEGORY = _nzbget_client.get("category") or "tv"
            settings.NZBGET_CATEGORY_BACKLOG = _nzbget_client.get("category_backlog") or settings.NZBGET_CATEGORY
            settings.NZBGET_CATEGORY_ANIME = _nzbget_client.get("category_anime") or "anime"
            settings.NZBGET_CATEGORY_ANIME_BACKLOG = _nzbget_client.get("category_anime_backlog") or settings.NZBGET_CATEGORY_ANIME
            settings.NZBGET_HOST = _nzbget_client.get("host") or ""
            settings.NZBGET_USE_HTTPS = str(_nzbget_client.get("use_https", "")).lower() in {"1", "true", "yes", "on"}
            try:
                settings.NZBGET_PRIORITY = int(_nzbget_client.get("priority") if _nzbget_client.get("priority") not in (None, "") else 100)
            except (TypeError, ValueError):
                settings.NZBGET_PRIORITY = 100
            if settings.NZBGET_PASSWORD:
                logger.censored_items[("CLIENTS", "nzbget.password")] = settings.NZBGET_PASSWORD
        else:
            settings.NZBGET_USERNAME = peek_setting_str(settings.CFG, "NZBget", "nzbget_username", "nzbget", censor_log=True)
            settings.NZBGET_PASSWORD = peek_setting_str(settings.CFG, "NZBget", "nzbget_password", "tegbzn6789", censor_log=True)
            settings.NZBGET_CATEGORY = peek_setting_str(settings.CFG, "NZBget", "nzbget_category", "tv")
            settings.NZBGET_CATEGORY_BACKLOG = peek_setting_str(settings.CFG, "NZBget", "nzbget_category_backlog", settings.NZBGET_CATEGORY)
            settings.NZBGET_CATEGORY_ANIME = peek_setting_str(settings.CFG, "NZBget", "nzbget_category_anime", "anime")
            settings.NZBGET_CATEGORY_ANIME_BACKLOG = peek_setting_str(settings.CFG, "NZBget", "nzbget_category_anime_backlog", settings.NZBGET_CATEGORY_ANIME)
            settings.NZBGET_HOST = peek_setting_str(settings.CFG, "NZBget", "nzbget_host")
            settings.NZBGET_USE_HTTPS = peek_setting_bool(settings.CFG, "NZBget", "nzbget_use_https")
            settings.NZBGET_PRIORITY = peek_setting_int(settings.CFG, "NZBget", "nzbget_priority", 100)
        if settings.NZBGET_PRIORITY not in (-100, -50, 0, 50, 100, 900):
            settings.NZBGET_PRIORITY = 100

        _torrent_client = None
        if isinstance(_clients, dict) and settings.TORRENT_METHOD and settings.TORRENT_METHOD not in ("blackhole",):
            _torrent_client = _clients.get(settings.TORRENT_METHOD)

        if settings.TORRENT_METHOD == "download_station" and isinstance(_torrent_client, dict):
            # DSM section is host/user/pass/path only — do not pull qbit-style leftovers.
            settings.TORRENT_HOST = _torrent_client.get("host") or ""
            settings.TORRENT_USERNAME = _torrent_client.get("username") or ""
            settings.TORRENT_PASSWORD = _torrent_client.get("password") or ""
            settings.TORRENT_PATH = _torrent_client.get("path") or ""
            settings.TORRENT_PATH_INCOMPLETE = ""
            settings.TORRENT_SEED_TIME = 0
            settings.TORRENT_PAUSED = False
            settings.TORRENT_HIGH_BANDWIDTH = False
            settings.TORRENT_LABEL = ""
            settings.TORRENT_LABEL_ANIME = ""
            settings.TORRENT_VERIFY_CERT = False
            settings.TORRENT_RPCURL = "transmission"
            settings.TORRENT_AUTH_TYPE = ""
            if settings.TORRENT_PASSWORD:
                logger.censored_items[("CLIENTS", "download_station.password")] = settings.TORRENT_PASSWORD
        elif isinstance(_torrent_client, dict) and (_torrent_client.get("host") or _torrent_client.get("username") or _torrent_client.get("password")):
            settings.TORRENT_USERNAME = _torrent_client.get("username") or ""
            settings.TORRENT_PASSWORD = _torrent_client.get("password") or ""
            settings.TORRENT_HOST = _torrent_client.get("host") or ""
            settings.TORRENT_PATH = _torrent_client.get("path") or ""
            settings.TORRENT_PATH_INCOMPLETE = _torrent_client.get("path_incomplete") or ""
            try:
                settings.TORRENT_SEED_TIME = int(_torrent_client.get("seed_time") or 0)
            except (TypeError, ValueError):
                settings.TORRENT_SEED_TIME = 0
            settings.TORRENT_PAUSED = str(_torrent_client.get("paused", "")).lower() in {"1", "true", "yes", "on"}
            settings.TORRENT_HIGH_BANDWIDTH = str(_torrent_client.get("high_bandwidth", "")).lower() in {"1", "true", "yes", "on"}
            settings.TORRENT_LABEL = _torrent_client.get("label") or ""
            settings.TORRENT_LABEL_ANIME = _torrent_client.get("label_anime") or ""
            settings.TORRENT_VERIFY_CERT = str(_torrent_client.get("verify_cert", "")).lower() in {"1", "true", "yes", "on"}
            settings.TORRENT_RPCURL = _torrent_client.get("rpcurl") or "transmission"
            settings.TORRENT_AUTH_TYPE = _torrent_client.get("auth_type") or ""
            if settings.TORRENT_PASSWORD:
                logger.censored_items[("CLIENTS", f"{settings.TORRENT_METHOD}.password")] = settings.TORRENT_PASSWORD
        else:
            settings.TORRENT_USERNAME = peek_setting_str(settings.CFG, "TORRENT", "torrent_username", censor_log=True)
            settings.TORRENT_PASSWORD = peek_setting_str(settings.CFG, "TORRENT", "torrent_password", censor_log=True)
            settings.TORRENT_HOST = peek_setting_str(settings.CFG, "TORRENT", "torrent_host")
            settings.TORRENT_PATH = peek_setting_str(settings.CFG, "TORRENT", "torrent_path")
            settings.TORRENT_PATH_INCOMPLETE = peek_setting_str(settings.CFG, "TORRENT", "torrent_path_incomplete")

            # Fix duplicated options
            if settings.TORRENT_METHOD.startswith("deluge"):
                deluge_download_dir = peek_setting_str(settings.CFG, "TORRENT", "torrent_download_dir_deluge")
                deluge_complete_dir = peek_setting_str(settings.CFG, "TORRENT", "torrent_complete_dir_deluge")
                settings.TORRENT_PATH = deluge_complete_dir or settings.TORRENT_PATH
                if deluge_download_dir and not settings.TORRENT_PATH_INCOMPLETE:
                    settings.TORRENT_PATH_INCOMPLETE = deluge_download_dir

            settings.TORRENT_SEED_TIME = peek_setting_int(settings.CFG, "TORRENT", "torrent_seed_time", min_val=-1)
            settings.TORRENT_PAUSED = peek_setting_bool(settings.CFG, "TORRENT", "torrent_paused")
            settings.TORRENT_HIGH_BANDWIDTH = peek_setting_bool(settings.CFG, "TORRENT", "torrent_high_bandwidth")
            settings.TORRENT_LABEL = peek_setting_str(settings.CFG, "TORRENT", "torrent_label")
            settings.TORRENT_LABEL_ANIME = peek_setting_str(settings.CFG, "TORRENT", "torrent_label_anime")
            settings.TORRENT_VERIFY_CERT = peek_setting_bool(settings.CFG, "TORRENT", "torrent_verify_cert")
            settings.TORRENT_RPCURL = peek_setting_str(settings.CFG, "TORRENT", "torrent_rpcurl", "transmission")
            settings.TORRENT_AUTH_TYPE = peek_setting_str(settings.CFG, "TORRENT", "torrent_auth_type")

        _ds_client = _clients.get("download_station") if isinstance(_clients, dict) else None
        if isinstance(_ds_client, dict) and (_ds_client.get("host") or _ds_client.get("username")):
            settings.SYNOLOGY_DSM_HOST = _ds_client.get("host") or ""
            settings.SYNOLOGY_DSM_USERNAME = _ds_client.get("username") or ""
            settings.SYNOLOGY_DSM_PASSWORD = _ds_client.get("password") or ""
            settings.SYNOLOGY_DSM_PATH = _ds_client.get("path") or ""
            if settings.SYNOLOGY_DSM_PASSWORD:
                logger.censored_items[("CLIENTS", "download_station.password")] = settings.SYNOLOGY_DSM_PASSWORD
        else:
            settings.SYNOLOGY_DSM_HOST = peek_setting_str(settings.CFG, "Synology", "host")
            settings.SYNOLOGY_DSM_USERNAME = peek_setting_str(settings.CFG, "Synology", "username", censor_log=True)
            settings.SYNOLOGY_DSM_PASSWORD = peek_setting_str(settings.CFG, "Synology", "password", censor_log=True)
            settings.SYNOLOGY_DSM_PATH = peek_setting_str(settings.CFG, "Synology", "path")

        helpers.manage_torrents_url(reset=True)

        # Notifier / Trakt / media-server settings come from [NOTIFIERS] via bootstrap_plugins()
        # (sync_legacy_maps_to_settings). Do not check_setting_* legacy sections here — that recreates empties.
        # use_synoindex may still linger under [Synology] until migrate; peek only.
        settings.USE_SYNOINDEX = peek_setting_bool(settings.CFG, "Synology", "use_synoindex")

        settings.FLARESOLVERR_URI = check_setting_str(settings.CFG, "General", "flaresolverr_uri")

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
        settings.SUBTITLES_FOREIGN_ONLY = check_setting_bool(settings.CFG, "Subtitles", "subtitles_foreign_only")
        settings.SUBTITLES_FINDER_FREQUENCY = check_setting_int(settings.CFG, "Subtitles", "subtitles_finder_frequency", 1, min_val=1)
        settings.SUBTITLES_MULTI = check_setting_bool(settings.CFG, "Subtitles", "subtitles_multi", True)
        settings.SUBTITLES_KEEP_ONLY_WANTED = check_setting_bool(settings.CFG, "Subtitles", "subtitles_keep_only_wanted")
        settings.SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(settings.CFG, "Subtitles", "subtitles_extra_scripts").split("|") if x.strip()]

        settings.ADDIC7ED_USER = check_setting_str(settings.CFG, "Subtitles", "addic7ed_username", censor_log=True)
        settings.ADDIC7ED_PASS = check_setting_str(settings.CFG, "Subtitles", "addic7ed_password", censor_log=True)

        settings.ITASA_USER = check_setting_str(settings.CFG, "Subtitles", "itasa_username", censor_log=True)
        settings.ITASA_PASS = check_setting_str(settings.CFG, "Subtitles", "itasa_password", censor_log=True)

        settings.OPENSUBTITLES_USER = check_setting_str(settings.CFG, "Subtitles", "opensubtitles_username", censor_log=True)
        settings.OPENSUBTITLES_PASS = check_setting_str(settings.CFG, "Subtitles", "opensubtitles_password", censor_log=True)
        settings.OPENSUBTITLESCOM_USER = check_setting_str(settings.CFG, "Subtitles", "opensubtitlescom_username", censor_log=True)
        settings.OPENSUBTITLESCOM_PASS = check_setting_str(settings.CFG, "Subtitles", "opensubtitlescom_password", censor_log=True)

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

        # Prefer [METADATA][[id]] bools (packed for interim UI); peek General only — never recreate metadata_*.
        from sickchill.plugins.metadata.config import (
            DEFAULT_PACKED as _METADATA_DEFAULT_PACKED,
            packed_from_metadata_or_general,
        )

        settings.METADATA_KODI = packed_from_metadata_or_general(settings.CFG, "kodi", "metadata_kodi", _METADATA_DEFAULT_PACKED)
        settings.METADATA_MEDIABROWSER = packed_from_metadata_or_general(settings.CFG, "mediabrowser", "metadata_mediabrowser", _METADATA_DEFAULT_PACKED)
        settings.METADATA_PS3 = packed_from_metadata_or_general(settings.CFG, "sony_ps3", "metadata_ps3", _METADATA_DEFAULT_PACKED)
        settings.METADATA_WDTV = packed_from_metadata_or_general(settings.CFG, "wdtv", "metadata_wdtv", _METADATA_DEFAULT_PACKED)
        settings.METADATA_TIVO = packed_from_metadata_or_general(settings.CFG, "tivo", "metadata_tivo", _METADATA_DEFAULT_PACKED)
        settings.METADATA_MEDE8ER = packed_from_metadata_or_general(settings.CFG, "mede8er", "metadata_mede8er", _METADATA_DEFAULT_PACKED)

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
        settings.ENDED_SHOWS_UPDATE_INTERVAL = check_setting_int(settings.CFG, "General", "ended_shows_update_interval", 14, min_val=-1, max_val=365)
        settings.SHOW_DISK_REFRESH_DAYS = check_setting_int(settings.CFG, "General", "show_disk_refresh_days", 7, min_val=-1, max_val=365)
        settings.NO_LGMARGIN = check_setting_bool(settings.CFG, "GUI", "no_lgmargin", True)

        if check_section(settings.CFG, "Shares"):
            settings.WINDOWS_SHARES.update(settings.CFG["Shares"])

        # initialize NZB and TORRENT providers
        settings.providerList = providers.makeProviderList()

        # Prefer [PROVIDERS] customs (type=newznab/torrentrss); fall back to legacy blobs via peek (no create).
        from sickchill.plugins.providers.config import custom_providers_from_cfg, providers_section_has_customs

        if providers_section_has_customs(settings.CFG):
            settings.newznab_provider_list, settings.torrent_rss_provider_list = custom_providers_from_cfg(settings.CFG)
            settings.NEWZNAB_DATA = "!!!".join(x.config_string() for x in settings.newznab_provider_list)
        else:
            settings.NEWZNAB_DATA = peek_setting_str(settings.CFG, "Newznab", "newznab_data", "")
            settings.newznab_provider_list = NewznabProvider.providers_list(settings.NEWZNAB_DATA)
            torrentrss_data = peek_setting_str(settings.CFG, "TorrentRss", "torrentrss_data", "")
            settings.torrent_rss_provider_list = TorrentRssProvider.providers_list(torrentrss_data)

        # Apply [PROVIDERS][[id]] (peek legacy [ID] without recreating empty sections).
        from sickchill.plugins.providers.config import apply_providers_from_cfg

        apply_providers_from_cfg(settings.CFG)

        try:
            from sickchill.oldbeard.providers.jackett import warn_jackett_newznab_overlap

            warn_jackett_newznab_overlap()
        except Exception as error:
            logger.debug(f"Jackett/Newznab overlap check skipped: {error}")

        providers.check_enabled_providers()

        if not os.path.isfile(settings.CONFIG_FILE):
            logger.debug(f"Unable to find ${settings.CONFIG_FILE}, all settings will be default!")
            save_config()

        # initialize the main SC database
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

        # One-shot plugin bootstrap: discover → migrate → [NOTIFIERS]/[CLIENTS]/[METADATA] → sync settings.*
        try:
            from sickchill.plugins.bootstrap import bootstrap_plugins

            if bootstrap_plugins():
                save_config()
        except Exception as error:
            logger.exception(f"Plugin manager failed to start: {error}")

        # After NOTIFIERS sync: blank revoked stock Trakt Client IDs from older installs.
        try:
            from sickchill.oldbeard.trakt_api.trakt import clear_revoked_trakt_defaults, refresh_trakt_pin_url

            if clear_revoked_trakt_defaults():
                logger.warning(
                    _(
                        "Cleared revoked built-in Trakt Client ID. Create a Trakt VIP API app and paste Client ID/Secret under Config → General → Indexer / Data."
                    )
                )
            else:
                refresh_trakt_pin_url()
        except Exception as error:
            logger.debug(f"Trakt revoked-default check skipped: {error}")

        # Build metadata_provider_dict AFTER bootstrap so sync'd METADATA_* packed values apply.
        from sickchill.plugins.metadata.config import refresh_metadata_provider_dict

        refresh_metadata_provider_dict()

        # initialize schedulers
        # updaters
        settings.versionCheckScheduler = scheduler.Scheduler(
            update_manager.UpdateManager(), cycleTime=datetime.timedelta(hours=settings.UPDATE_FREQUENCY), threadName="CHECKVERSION", silent=False
        )

        settings.showQueueScheduler = scheduler.Scheduler(show_queue.ShowQueue(), cycleTime=datetime.timedelta(seconds=5), threadName="SHOWQUEUE")

        # Minute from process start (not stored); ShowUpdater may nudge it +0..20 after each run.
        _showupdate_minute = sc_now().minute
        settings.showUpdateScheduler = scheduler.Scheduler(
            show_updater.ShowUpdater(),
            run_delay=datetime.timedelta(seconds=20),
            cycleTime=datetime.timedelta(hours=1),
            start_time=datetime.time(hour=settings.SHOWUPDATE_HOUR, minute=_showupdate_minute),
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

        search_intervals = {"30m": 30, "90m": 90, "4h": 4 * 60, "8h": 8 * 60, "daily": 24 * 60}
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

            # Stop queue *workers* (currentItem), not only their scheduler threads.
            # A stuck SHOWQUEUE-REFRESH otherwise survives join(10) on SHOWQUEUE.
            for queue_scheduler in (
                settings.showQueueScheduler,
                settings.searchQueueScheduler,
                settings.postProcessorTaskScheduler,
            ):
                action = getattr(queue_scheduler, "action", None)
                if action is not None and hasattr(action, "stop_current_item"):
                    try:
                        action.stop_current_item(timeout=10)
                    except Exception as error:
                        logger.warning(f"Error stopping {getattr(queue_scheduler, 'name', 'queue')} current item: {error}")

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


def sig_handler(signum=None, *args, **kwargs):
    if not (signum is None):
        logger.info(f"Signal {signum} caught, saving and exiting...")
        Shutdown.stop(settings.PID)


def save_all():
    # write all shows
    logger.info("Saving all shows to the database")
    for show in settings.show_list:
        show.save_to_db()

    # persist in-memory name cache (scene_names) in one write
    from sickchill.oldbeard import name_cache

    name_cache.save_all_cached_names()

    # save config
    logger.info("Saving config file to disk")
    save_config()


def save_config():
    new_config = ConfigObj(settings.CONFIG_FILE, encoding="UTF-8", indent_type="  ")

    # For passwords, you must include the word `password` in the item_name and add `helpers.encrypt(settings.ITEM_NAME, settings.ENCRYPTION_VERSION)` in save_config()
    # Provider settings live under [PROVIDERS][[id]]; write_providers_to_cfg owns them.

    new_config.update(
        {
            "General": {
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
                "tvdb_v4_apikey": settings.TVDB_V4_APIKEY,
                "tvdb_v4_pin": helpers.encrypt_config_value(settings.TVDB_V4_PIN or ""),
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
                "download_propers_window_days": int(settings.DOWNLOAD_PROPERS_WINDOW_DAYS),
                "randomize_providers": int(settings.RANDOMIZE_PROVIDERS),
                "check_propers_interval": settings.CHECK_PROPERS_INTERVAL,
                "allow_high_priority": int(settings.ALLOW_HIGH_PRIORITY),
                "skip_removed_files": int(settings.SKIP_REMOVED_FILES),
                "allowed_extensions": settings.ALLOWED_EXTENSIONS,
                "quality_default": int(settings.QUALITY_DEFAULT),
                "status_default": int(settings.STATUS_DEFAULT),
                "status_default_after": int(settings.STATUS_DEFAULT_AFTER),
                "season_folders_default": int(settings.SEASON_FOLDERS_DEFAULT),
                "indexer_default": int(settings.INDEXER_DEFAULT),
                "indexer_timeout": int(settings.INDEXER_TIMEOUT),
                "anime_default": int(settings.ANIME_DEFAULT),
                "scene_default": int(settings.SCENE_DEFAULT),
                "whitelist_default": ",".join(settings.WHITELIST_DEFAULT),
                "blacklist_default": ",".join(settings.BLACKLIST_DEFAULT),
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
                # metadata_* packed strings live under [METADATA]; write_metadata_to_cfg owns them.
                "backlog_days": int(settings.BACKLOG_DAYS),
                "backlog_missing_only": int(settings.BACKLOG_MISSING_ONLY),
                "root_dirs": settings.ROOT_DIRS or "",
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
                "show_disk_refresh_days": int(settings.SHOW_DISK_REFRESH_DAYS),
                "news_last_read": settings.NEWS_LAST_READ,
                "flaresolverr_uri": settings.FLARESOLVERR_URI,
            },
            "Cloudflare": {"auth_domain": settings.CF_AUTH_DOMAIN, "audience_policy": settings.CF_POLICY_AUD},
            "Shares": settings.WINDOWS_SHARES,
            # Blackhole / SABnzbd / NZBget / TORRENT / notifier / metadata / provider sections live under
            # [CLIENTS] / [NOTIFIERS] / [METADATA] / [PROVIDERS]; write_all_plugin_settings_to_cfg owns them.
            # Newznab / TorrentRss blobs are no longer written — customs live in PROVIDERS with type=.
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
                "subtitles_foreign_only": int(settings.SUBTITLES_FOREIGN_ONLY),
                "subtitles_finder_frequency": int(settings.SUBTITLES_FINDER_FREQUENCY),
                "subtitles_multi": int(settings.SUBTITLES_MULTI),
                "subtitles_extra_scripts": "|".join(settings.SUBTITLES_EXTRA_SCRIPTS),
                "subtitles_keep_only_wanted": int(settings.SUBTITLES_KEEP_ONLY_WANTED),
                "addic7ed_username": settings.ADDIC7ED_USER,
                "addic7ed_password": helpers.encrypt(settings.ADDIC7ED_PASS, settings.ENCRYPTION_VERSION),
                "itasa_username": settings.ITASA_USER,
                "itasa_password": helpers.encrypt(settings.ITASA_PASS, settings.ENCRYPTION_VERSION),
                "opensubtitles_username": settings.OPENSUBTITLES_USER,
                "opensubtitles_password": helpers.encrypt(settings.OPENSUBTITLES_PASS, settings.ENCRYPTION_VERSION),
                "opensubtitlescom_username": settings.OPENSUBTITLESCOM_USER,
                "opensubtitlescom_password": helpers.encrypt(settings.OPENSUBTITLESCOM_PASS, settings.ENCRYPTION_VERSION),
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
    # Plugin-backed settings live under [NOTIFIERS] / [CLIENTS] / [METADATA] / [PROVIDERS].
    try:
        from sickchill.plugins.bootstrap import write_all_plugin_settings_to_cfg
        from sickchill.plugins.manager import plugin_manager

        if "NOTIFIERS" in settings.CFG:
            new_config["NOTIFIERS"] = settings.CFG["NOTIFIERS"]
        if "CLIENTS" in settings.CFG:
            new_config["CLIENTS"] = settings.CFG["CLIENTS"]
        if "METADATA" in settings.CFG:
            new_config["METADATA"] = settings.CFG["METADATA"]
        if "PROVIDERS" in settings.CFG:
            new_config["PROVIDERS"] = settings.CFG["PROVIDERS"]
        # Leftover non-migrated kinds may still use [extensions].
        if "extensions" in settings.CFG:
            new_config["extensions"] = settings.CFG["extensions"]
        write_all_plugin_settings_to_cfg(new_config)
        # Keep runtime CFG / plugin manager in sync with what we just wrote so snatch
        # does not reuse a stale ClientPlugin ctx (empty username after save).
        settings.CFG = new_config
        plugin_manager._cfg = new_config
        plugin_manager._instances.clear()
    except Exception as error:
        logger.debug(f"Could not persist plugin settings: {error}")
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
        webbrowser.open(browserURL, 2)
    except Exception:
        try:
            webbrowser.open(browserURL, 1)
        except Exception:
            logger.exception("Unable to launch a browser")
