# coding=utf-8
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.
# Stdlib Imports
import datetime
import os
import platform
import random
import re
import shutil
import socket
import sys
from threading import Lock

# First Party Imports
from setup import setup_gettext, setup_lib_path

setup_lib_path()

# Third Party Imports
import rarfile
import requests
from adba import Connection as AniDBConnection
from configobj import ConfigObj
from tornado.locale import load_gettext_translations

# First Party Imports
import sickchill
from sickchill import show_updater
from sickchill.helper import setup_github
from sickchill.system.Shutdown import Shutdown

# Local Folder Imports
from . import (dailysearcher, databases, db, event_queue, helpers, image_cache, logger, naming, notifications_queue, post_processing_queue, properFinder,
               scene_exceptions, scheduler, search_queue, searchBacklog, show_queue, subtitles, traktChecker, versionChecker)
from .common import ARCHIVED, IGNORED, MULTI_EP_STRINGS, SD, SKIPPED, WANTED
from .config import check_section, check_setting_bool, check_setting_float, check_setting_int, check_setting_str, ConfigMigrator
from .numdict import NumDict

setup_gettext()

# Some strings come from metadata or libraries or 3rd party sites,
# So we need to pre-define them to get translations for them
dynamic_strings = (
    _('Drama'), _('Mystery'), _('Science-Fiction'), _('Crime'), _('Action'),
    _('Comedy'), _('Thriller'), _('Animation'), _('Family'), _('Fantasy'),
    _('Adventure'), _('Horror'), _('Film-Noir'), _('Sci-Fi'), _('Romance'),
    _('Sport'), _('War'), _('Biography'), _('History'), _('Music'), _('Western'),
    _('News'), _('Sitcom'), _('Reality-TV'), _('Documentary'), _('Game-Show'), _('Musical'),
    _('Talk-Show'), _('Science-Fiction')
)

# noinspection PyUnresolvedReferences
requests.packages.urllib3.disable_warnings()

PID = None
WINDOWS_SHARES = {}

CFG: ConfigObj
CFG2: ConfigObj
CONFIG_FILE = ""
CONFIG_FILE_NEW = ""
CONFIG_SPEC = ""

# This is the version of the config we EXPECT to find
CONFIG_VERSION = 8

# Default encryption version (0 for None)
ENCRYPTION_VERSION = 0
ENCRYPTION_SECRET = None

IMAGE_CACHE = None

PROG_DIR = '.'
MY_FULLNAME: str
LOCALE_DIR = 'locale'
MY_NAME: str
MY_ARGS = []
DATA_DIR = ''
CREATEPID = False
PIDFILE = ''

SITE_MESSAGES = {}

DAEMON = None
NO_RESIZE = False

TVDB_USER: str
TVDB_USER_KEY: str

# system events
events: event_queue.Events

# github
gh = None

# schedulers
dailySearchScheduler: scheduler.Scheduler
backlogSearchScheduler: searchBacklog.BacklogSearchScheduler
showUpdateScheduler: scheduler.Scheduler
versionCheckScheduler: scheduler.Scheduler
showQueueScheduler: scheduler.Scheduler
searchQueueScheduler: scheduler.Scheduler
properFinderScheduler: scheduler.Scheduler
autoPostProcessorScheduler: scheduler.Scheduler
postProcessorTaskScheduler: scheduler.Scheduler
subtitlesFinderScheduler: scheduler.Scheduler
traktCheckerScheduler: scheduler.Scheduler
notificationsTaskScheduler: scheduler.Scheduler

showList = []

VERSION_NOTIFY = False
AUTO_UPDATE = False
NOTIFY_ON_UPDATE = False
CUR_COMMIT_HASH: str
BRANCH = ''

GIT_RESET = True
GIT_REMOTE = ''
GIT_REMOTE_URL = ''
CUR_COMMIT_BRANCH = ''
GIT_ORG = 'SickChill'
GIT_REPO = 'SickChill'
GIT_USERNAME: str
GIT_TOKEN = ''
GIT_PATH = ''
DEVELOPER = False

NEWS_URL = 'https://sickchill.github.io/sickchill-news/news.md'
LOGO_URL = 'https://sickchill.github.io/images/ico/favicon-64.png'

NEWS_LAST_READ = None
NEWS_LATEST = None
NEWS_UNREAD = 0

NZB_DIR: str = ""
TORRENT_DIR: str = ""

INIT_LOCK = Lock()
MESSAGES_LOCK = Lock()
started = {}

LOG_DIR: str
LOG_NR = 5
LOG_SIZE = 10.0

SOCKET_TIMEOUT: int

WEB_PORT: int = 8080
WEB_LOG = False
WEB_ROOT: str
WEB_USERNAME: str
WEB_PASSWORD: str
WEB_HOST: str
WEB_IPV6 = False
WEB_COOKIE_SECRET: str
WEB_USE_GZIP = True

CF_AUTH_DOMAIN = ''
CF_POLICY_AUD = ''

DOWNLOAD_URL: str

HANDLE_REVERSE_PROXY = False
PROXY_SETTING = None
PROXY_INDEXERS = False
SSL_VERIFY = True

LOCALHOST_IP: str

CPU_PRESET = None

ANON_REDIRECT = None

API_KEY: str
API_ROOT: str

ENABLE_HTTPS = False
NOTIFY_ON_LOGIN = False
HTTPS_CERT: str
HTTPS_KEY: str

INDEXER_DEFAULT_LANGUAGE: str
EP_DEFAULT_DELETED_STATUS = None
LAUNCH_BROWSER = False
CACHE_DIR: str
ROOT_DIRS: str

TRASH_REMOVE_SHOW = False
TRASH_ROTATE_LOGS = False
IGNORE_BROKEN_SYMLINKS = False
SORT_ARTICLE = False
DEBUG = False
DBDEBUG = False
DISPLAY_ALL_SEASONS = True
DEFAULT_PAGE = 'home'

USE_LISTVIEW: bool = False

QUALITY_DEFAULT: int
QUALITY_ALLOW_HEVC: bool = False
STATUS_DEFAULT: int
STATUS_DEFAULT_AFTER: int
SEASON_FOLDERS_DEFAULT: bool = False
SUBTITLES_DEFAULT: bool = False
INDEXER_DEFAULT = 1
INDEXER_TIMEOUT: int
SCENE_DEFAULT: bool = False
ANIME_DEFAULT: bool = False
PROVIDER_ORDER = []
NAMING_MULTI_EP: bool = False
NAMING_ANIME_MULTI_EP: bool = False
NAMING_PATTERN: str
NAMING_ABD_PATTERN: str
NAMING_CUSTOM_ABD: bool = False
NAMING_SPORTS_PATTERN: str
NAMING_CUSTOM_SPORTS: bool = False
NAMING_ANIME_PATTERN: str
NAMING_CUSTOM_ANIME: bool = False
NAMING_FORCE_FOLDERS: bool = False
NAMING_STRIP_YEAR: bool = False
NAMING_ANIME: int

USE_NZBS: bool = False
USE_TORRENTS: bool = False

CLIENT_WEB_URLS: dict = dict()

DOWNLOAD_PROPERS: bool = False
CHECK_PROPERS_INTERVAL: int
ALLOW_HIGH_PRIORITY: bool = False
RANDOMIZE_PROVIDERS: bool = False

AUTOPOSTPROCESSOR_FREQUENCY: int
DAILYSEARCH_FREQUENCY = 40
UPDATE_FREQUENCY: int
BACKLOG_FREQUENCY: int
SHOWUPDATE_HOUR: int

DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY = 10
DEFAULT_DAILYSEARCH_FREQUENCY = 40
DEFAULT_BACKLOG_FREQUENCY = 21
DEFAULT_UPDATE_FREQUENCY = 1
DEFAULT_SHOWUPDATE_HOUR = random.randint(2, 4)

MIN_AUTOPOSTPROCESSOR_FREQUENCY = 1
MIN_DAILYSEARCH_FREQUENCY = 10
MIN_BACKLOG_FREQUENCY = 10
MIN_UPDATE_FREQUENCY = 1

BACKLOG_DAYS = 7

ADD_SHOWS_WO_DIR: bool = False
ADD_SHOWS_WITH_YEAR: bool = False
CREATE_MISSING_SHOW_DIRS: bool = False
RENAME_EPISODES: bool = False
AIRDATE_EPISODES: bool = False
FILE_TIMESTAMP_TIMEZONE = None
PROCESS_AUTOMATICALLY: bool = False
NO_DELETE: bool = False
USE_ICACLS = True
KEEP_PROCESSED_DIR: bool = False
PROCESS_METHOD: str
PROCESSOR_FOLLOW_SYMLINKS: bool = False
DELRARCONTENTS: bool = False
MOVE_ASSOCIATED_FILES: bool = False
DELETE_NON_ASSOCIATED_FILES: bool = False
POSTPONE_IF_SYNC_FILES = True
NFO_RENAME = True
TV_DOWNLOAD_DIR: str

SKIP_REMOVED_FILES: bool = False
ALLOWED_EXTENSIONS = "srt,nfo,srr,sfv"
USE_FREE_SPACE_CHECK = True

ANIMESUPPORT: bool = False
USE_ANIDB: bool = False
ANIDB_USERNAME: str
ANIDB_PASSWORD: str
ANIDB_USE_MYLIST: bool = False
ADBA_CONNECTION: AniDBConnection
ANIME_SPLIT_HOME: bool = False
ANIME_SPLIT_HOME_IN_TABS: bool = False

USE_SYNOINDEX: bool = False


GUI_NAME: str
GUI_LANG: str

HOME_LAYOUT: str
HISTORY_LAYOUT: str
HISTORY_LIMIT = 0
DISPLAY_SHOW_SPECIALS: bool = False
COMING_EPS_LAYOUT: str
COMING_EPS_DISPLAY_SNATCHED: bool = False
COMING_EPS_DISPLAY_PAUSED: bool = True
COMING_EPS_SORT: str
COMING_EPS_MISSED_RANGE: int
FUZZY_DATING: bool = False
TRIM_ZERO: bool = False
DATE_PRESET = None
TIME_PRESET = None
TIME_PRESET_W_SECONDS = None
TIMEZONE_DISPLAY = None
THEME_NAME: str
POSTER_SORTBY: str
POSTER_SORTDIR: bool = False
SICKCHILL_BACKGROUND: bool = False
SICKCHILL_BACKGROUND_PATH: str
FANART_BACKGROUND: bool = False
FANART_BACKGROUND_OPACITY: int
CUSTOM_CSS: bool = False
CUSTOM_CSS_PATH: str

USE_SUBTITLES: bool = False
SUBTITLES_INCLUDE_SPECIALS: bool = False
SUBTITLES_LANGUAGES = []
SUBTITLES_DIR = ''
SUBTITLES_SERVICES_LIST = []
SUBTITLES_SERVICES_ENABLED = []
SUBTITLES_HISTORY: bool = False
SUBTITLES_PERFECT_MATCH: bool = False
EMBEDDED_SUBTITLES_ALL: bool = False
SUBTITLES_HEARING_IMPAIRED: bool = False
SUBTITLES_FINDER_FREQUENCY = 1
SUBTITLES_MULTI: bool = False
SUBTITLES_EXTRA_SCRIPTS = []
SUBTITLES_KEEP_ONLY_WANTED: bool = False

USE_FAILED_DOWNLOADS: bool = False
DELETE_FAILED: bool = False

BACKLOG_MISSING_ONLY: bool = False

EXTRA_SCRIPTS = []

IGNORE_WORDS = "german,french,core2hd,dutch,swedish,reenc,MrLss"

TRACKERS_LIST = "udp://coppersurfer.tk:6969/announce,udp://open.demonii.com:1337,"
TRACKERS_LIST += "udp://exodus.desync.com:6969,udp://9.rarbg.me:2710/announce,"
TRACKERS_LIST += "udp://glotorrents.pw:6969/announce,udp://tracker.openbittorrent.com:80/announce,"
TRACKERS_LIST += "udp://9.rarbg.to:2710/announce"

REQUIRE_WORDS = ""
PREFER_WORDS = ""
IGNORED_SUBS_LIST = "dk,fin,heb,kor,nor,nordic,pl,swe"
SYNC_FILES = "!sync,lftp-pget-status,bts,!qb,!qB"

CALENDAR_UNPROTECTED: bool = False
CALENDAR_ICONS: bool = False
NO_RESTART: bool = False

TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'
# TRAKT_API_KEY = 'd4161a7a106424551add171e5470112e4afdaf2438e6ef2fe0548edc75924868'

TRAKT_API_KEY = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
TRAKT_API_SECRET = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
TRAKT_PIN_URL = 'https://trakt.tv/pin/4562'
TRAKT_OAUTH_URL = 'https://trakt.tv/'
TRAKT_API_URL = 'https://api-v2launch.trakt.tv/'

FANART_API_KEY = '9b3afaf26f6241bdb57d6cc6bd798da7'

SHOWS_RECENT = []

__INITIALIZED__ = {}

UNPACK_DISABLED = 0
UNPACK_PROCESS_CONTENTS = 1
UNPACK_PROCESS_INTACT = 2

unpackStrings = NumDict({
    UNPACK_DISABLED: _('Ignore (do not process contents)'),
    UNPACK_PROCESS_CONTENTS: _('Unpack (process contents)'),
    UNPACK_PROCESS_INTACT: _('Treat as video (process archive as-is)')
})

UNPACK = UNPACK_DISABLED
UNPACK_DIR = ''
UNRAR_TOOL = rarfile.UNRAR_TOOL
ALT_UNRAR_TOOL = rarfile.ALT_TOOL

ENDED_SHOWS_UPDATE_INTERVAL = 7


def get_backlog_cycle_time():
    cycletime = DAILYSEARCH_FREQUENCY * 2 + 7
    return max([cycletime, 720])


def initialize(consoleLogging=True):
    with INIT_LOCK:

        global BRANCH, GIT_RESET, GIT_REMOTE, GIT_REMOTE_URL, CUR_COMMIT_HASH, CUR_COMMIT_BRANCH, LOG_DIR, LOG_NR, LOG_SIZE, WEB_PORT, WEB_LOG,\
            ENCRYPTION_VERSION, ENCRYPTION_SECRET, WEB_ROOT, WEB_USERNAME, WEB_PASSWORD, WEB_HOST, WEB_IPV6, WEB_COOKIE_SECRET, WEB_USE_GZIP, API_KEY,\
            ENABLE_HTTPS, HTTPS_CERT, HTTPS_KEY, HANDLE_REVERSE_PROXY, USE_NZBS, USE_TORRENTS, DOWNLOAD_PROPERS, RANDOMIZE_PROVIDERS, \
            CHECK_PROPERS_INTERVAL, ALLOW_HIGH_PRIORITY, NOTIFY_ON_LOGIN, backlogSearchScheduler, BACKLOG_FREQUENCY, \
            traktCheckerScheduler, \
            MIN_BACKLOG_FREQUENCY, SKIP_REMOVED_FILES, ALLOWED_EXTENSIONS, SITE_MESSAGES, showUpdateScheduler, \
            INDEXER_DEFAULT_LANGUAGE, EP_DEFAULT_DELETED_STATUS, LAUNCH_BROWSER, TRASH_REMOVE_SHOW, TRASH_ROTATE_LOGS, IGNORE_BROKEN_SYMLINKS, SORT_ARTICLE, \
            INDEXER_DEFAULT, INDEXER_TIMEOUT, QUALITY_DEFAULT, QUALITY_ALLOW_HEVC, \
            SEASON_FOLDERS_DEFAULT, \
            SUBTITLES_DEFAULT, STATUS_DEFAULT, STATUS_DEFAULT_AFTER, versionCheckScheduler, VERSION_NOTIFY, AUTO_UPDATE, NOTIFY_ON_UPDATE, \
            PROCESS_AUTOMATICALLY, NO_DELETE, USE_ICACLS, UNPACK, \
            CPU_PRESET, UNPACK_DIR, UNRAR_TOOL, ALT_UNRAR_TOOL, KEEP_PROCESSED_DIR, PROCESS_METHOD, PROCESSOR_FOLLOW_SYMLINKS, DELRARCONTENTS, \
            TV_DOWNLOAD_DIR, UPDATE_FREQUENCY, showQueueScheduler, searchQueueScheduler, postProcessorTaskScheduler, ROOT_DIRS, CACHE_DIR, \
            TIMEZONE_DISPLAY, NAMING_PATTERN, NAMING_MULTI_EP, NAMING_ANIME_MULTI_EP, NAMING_FORCE_FOLDERS, NAMING_ABD_PATTERN, NAMING_CUSTOM_ABD, \
            NAMING_SPORTS_PATTERN, NAMING_CUSTOM_SPORTS, NAMING_ANIME_PATTERN, NAMING_CUSTOM_ANIME, NAMING_STRIP_YEAR, RENAME_EPISODES, AIRDATE_EPISODES, \
            FILE_TIMESTAMP_TIMEZONE, properFinderScheduler, PROVIDER_ORDER, autoPostProcessorScheduler, EXTRA_SCRIPTS, DAILYSEARCH_FREQUENCY, USE_SYNOINDEX, \
            GIT_PATH, MOVE_ASSOCIATED_FILES, DELETE_NON_ASSOCIATED_FILES, SYNC_FILES, POSTPONE_IF_SYNC_FILES, dailySearchScheduler, \
            NFO_RENAME, GUI_NAME, HOME_LAYOUT, HISTORY_LAYOUT, DISPLAY_SHOW_SPECIALS, COMING_EPS_LAYOUT, COMING_EPS_SORT, COMING_EPS_DISPLAY_PAUSED, \
            COMING_EPS_DISPLAY_SNATCHED, COMING_EPS_MISSED_RANGE, FUZZY_DATING, TRIM_ZERO, DATE_PRESET, TIME_PRESET, TIME_PRESET_W_SECONDS, THEME_NAME, \
            POSTER_SORTBY, POSTER_SORTDIR, HISTORY_LIMIT, CREATE_MISSING_SHOW_DIRS, ADD_SHOWS_WO_DIR, USE_FREE_SPACE_CHECK, IGNORE_WORDS, TRACKERS_LIST, \
            IGNORED_SUBS_LIST, REQUIRE_WORDS, PREFER_WORDS, CALENDAR_UNPROTECTED, CALENDAR_ICONS, NO_RESTART, USE_SUBTITLES,\
            SUBTITLES_INCLUDE_SPECIALS, SUBTITLES_LANGUAGES, SUBTITLES_DIR, SUBTITLES_SERVICES_LIST, SUBTITLES_SERVICES_ENABLED, SUBTITLES_HISTORY, \
            SUBTITLES_FINDER_FREQUENCY, SUBTITLES_MULTI, SUBTITLES_KEEP_ONLY_WANTED, EMBEDDED_SUBTITLES_ALL, SUBTITLES_EXTRA_SCRIPTS, SUBTITLES_PERFECT_MATCH,\
            subtitlesFinderScheduler, SUBTITLES_HEARING_IMPAIRED, USE_FAILED_DOWNLOADS, DELETE_FAILED, BACKLOG_MISSING_ONLY, ANON_REDIRECT, LOCALHOST_IP, \
            DEBUG, DBDEBUG, DEFAULT_PAGE, PROXY_SETTING, PROXY_INDEXERS, AUTOPOSTPROCESSOR_FREQUENCY, SHOWUPDATE_HOUR, ANIME_DEFAULT, NAMING_ANIME, \
            USE_ANIDB, ANIDB_USERNAME, ANIDB_PASSWORD, ANIDB_USE_MYLIST, ANIME_SPLIT_HOME, ANIME_SPLIT_HOME_IN_TABS, SCENE_DEFAULT, \
            DOWNLOAD_URL, BACKLOG_DAYS, GIT_USERNAME, GIT_TOKEN, DEVELOPER, DISPLAY_ALL_SEASONS, SSL_VERIFY, NEWS_LAST_READ, ADD_SHOWS_WITH_YEAR, \
            NEWS_LATEST, SOCKET_TIMEOUT, GUI_LANG, SICKCHILL_BACKGROUND, NZB_DIR, TORRENT_DIR, \
            SICKCHILL_BACKGROUND_PATH, FANART_BACKGROUND, FANART_BACKGROUND_OPACITY, CUSTOM_CSS, CUSTOM_CSS_PATH, \
            ENDED_SHOWS_UPDATE_INTERVAL, IMAGE_CACHE, CF_AUTH_DOMAIN, CF_POLICY_AUD, TVDB_USER, TVDB_USER_KEY, notificationsTaskScheduler, USE_LISTVIEW

        if __INITIALIZED__:
            return False

        check_section(CFG, 'General')

        # Need to be before any passwords
        ENCRYPTION_VERSION = check_setting_int(CFG, 'General', 'encryption_version', min_val=0, max_val=2)
        ENCRYPTION_SECRET = check_setting_str(CFG, 'General', 'encryption_secret', helpers.generateCookieSecret(), censor_log=True)

        # git login info
        GIT_USERNAME = check_setting_str(CFG, 'General', 'git_username')
        GIT_TOKEN = check_setting_str(CFG, 'General', 'git_token_password', censor_log=True)  # encryption needed
        DEVELOPER = check_setting_bool(CFG, 'General', 'developer')

        # debugging
        DEBUG = check_setting_bool(CFG, 'General', 'debug')
        DBDEBUG = check_setting_bool(CFG, 'General', 'dbdebug')

        DEFAULT_PAGE = check_setting_str(CFG, 'General', 'default_page', 'home')
        if DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            DEFAULT_PAGE = 'home'

        LOG_DIR = os.path.normpath(os.path.join(DATA_DIR, 'Logs'))
        LOG_NR = check_setting_int(CFG, 'General', 'log_nr', 5, min_val=1)  # Default to 5 backup file (sickchill.log.x)
        LOG_SIZE = check_setting_float(CFG, 'General', 'log_size', 10.0, min_val=0.5)  # Default to max 10MB per logfile

        if LOG_SIZE > 100:
            LOG_SIZE = 10.0
        fileLogging = True

        if not helpers.makeDir(LOG_DIR):
            sys.stderr.write("!!! No log folder, logging to screen only!\n")
            fileLogging = False

        # init logging
        logger.init_logging(console_logging=consoleLogging, file_logging=fileLogging, debug_logging=DEBUG, database_logging=DBDEBUG)

        # Initializes sickbeard.gh
        setup_github()

        # git reset on update
        GIT_RESET = check_setting_bool(CFG, 'General', 'git_reset', True)

        # current git branch
        BRANCH = check_setting_str(CFG, 'General', 'branch')

        # git_remote
        GIT_REMOTE = check_setting_str(CFG, 'General', 'git_remote', 'origin')
        GIT_REMOTE_URL = check_setting_str(CFG, 'General', 'git_remote_url',
                                           'https://github.com/{0}/{1}.git'.format(GIT_ORG, GIT_REPO))

        if 'rage' in GIT_REMOTE_URL.lower():
            GIT_REMOTE_URL = 'https://github.com/{0}/{1}.git'.format(GIT_ORG, GIT_REPO)

        # current commit hash
        CUR_COMMIT_HASH = check_setting_str(CFG, 'General', 'cur_commit_hash')

        # current commit branch
        CUR_COMMIT_BRANCH = check_setting_str(CFG, 'General', 'cur_commit_branch')

        GUI_NAME = check_setting_str(CFG, 'GUI', 'gui_name', 'slick')
        GUI_LANG = check_setting_str(CFG, 'GUI', 'language')

        setup_gettext(GUI_LANG)

        load_gettext_translations(LOCALE_DIR, 'messages')

        CACHE_DIR = os.path.normpath(os.path.join(PROG_DIR, "gui", GUI_NAME, "cache"))
        if platform.system() != 'Windows':  # Not sure if this will work on windows yet, but it works on linux
            DATA_CACHE = os.path.join(DATA_DIR, 'cache')
            try:
                if not os.path.isdir(DATA_CACHE):
                    if os.path.isdir(CACHE_DIR) and not os.path.islink(CACHE_DIR):
                        helpers.moveFile(CACHE_DIR, DATA_CACHE)

                if not os.path.isdir(DATA_CACHE):
                    helpers.makeDir(DATA_CACHE)

                if os.path.isdir(DATA_CACHE) and not os.path.islink(CACHE_DIR):
                    if os.path.isdir(CACHE_DIR):
                        shutil.rmtree(CACHE_DIR)

                    os.symlink(DATA_CACHE, CACHE_DIR)
            except Exception as e:
                print(e)

        # Check if we need to perform a restore of the cache folder
        try:
            restoreDir = os.path.join(DATA_DIR, 'restore')
            if os.path.exists(restoreDir) and os.path.exists(os.path.join(restoreDir, 'cache')):
                def restoreCache(srcDir, dstDir):
                    def path_leaf(path):
                        head, tail = os.path.split(path)
                        return tail or os.path.basename(head)

                    try:
                        if os.path.isdir(dstDir):
                            # noinspection PyTypeChecker
                            bakFilename = '{0}-{1}'.format(path_leaf(dstDir), datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S'))
                            shutil.move(dstDir, os.path.join(os.path.dirname(dstDir), bakFilename))

                        shutil.move(srcDir, dstDir)
                        logger.info("Restore: restoring cache successful")
                    except Exception as er:
                        logger.exception("Restore: restoring cache failed: {0}".format(er))

                restoreCache(os.path.join(restoreDir, 'cache'), CACHE_DIR)
        except Exception as e:
            logger.exception("Restore: restoring cache failed: {0}".format(str(e)))
        finally:
            if os.path.exists(os.path.join(DATA_DIR, 'restore')):
                try:
                    shutil.rmtree(os.path.join(DATA_DIR, 'restore'))
                except Exception as e:
                    logger.exception("Restore: Unable to remove the restore directory: {0}".format(str(e)))

                for cleanupDir in ['mako', 'sessions', 'indexers', 'rss']:
                    try:
                        shutil.rmtree(os.path.join(CACHE_DIR, cleanupDir))
                    except Exception as e:
                        if cleanupDir not in ['rss', 'sessions', 'indexers']:
                            logger.warning("Restore: Unable to remove the cache/{0} directory: {1}".format(cleanupDir, str(e)))

        IMAGE_CACHE = image_cache.ImageCache()
        THEME_NAME = check_setting_str(CFG, 'GUI', 'theme_name', 'dark')
        SICKCHILL_BACKGROUND = check_setting_bool(CFG, 'GUI', 'sickchill_background')
        SICKCHILL_BACKGROUND_PATH = check_setting_str(CFG, 'GUI', 'sickchill_background_path')
        FANART_BACKGROUND = check_setting_bool(CFG, 'GUI', 'fanart_background', True)
        FANART_BACKGROUND_OPACITY = check_setting_float(CFG, 'GUI', 'fanart_background_opacity', 0.4, min_val=0.1, max_val=1.0)
        CUSTOM_CSS = check_setting_bool(CFG, 'GUI', 'custom_css')
        CUSTOM_CSS_PATH = check_setting_str(CFG, 'GUI', 'custom_css_path')

        SOCKET_TIMEOUT = check_setting_int(CFG, 'General', 'socket_timeout', 30, min_val=0)
        socket.setdefaulttimeout(SOCKET_TIMEOUT)

        try:
            WEB_PORT = check_setting_int(CFG, 'General', 'web_port', 8081, min_val=21, max_val=65535)
        except Exception:
            WEB_PORT = 8081

        WEB_HOST = check_setting_str(CFG, 'General', 'web_host', '0.0.0.0')
        WEB_IPV6 = check_setting_bool(CFG, 'General', 'web_ipv6')
        WEB_ROOT = check_setting_str(CFG, 'General', 'web_root').rstrip("/")
        WEB_LOG = check_setting_bool(CFG, 'General', 'web_log')
        WEB_USERNAME = check_setting_str(CFG, 'General', 'web_username', censor_log=True)
        WEB_PASSWORD = check_setting_str(CFG, 'General', 'web_password', censor_log=True)
        WEB_COOKIE_SECRET = check_setting_str(CFG, 'General', 'web_cookie_secret', helpers.generateCookieSecret(), censor_log=True)
        if not WEB_COOKIE_SECRET:
            WEB_COOKIE_SECRET = helpers.generateCookieSecret()

        CF_AUTH_DOMAIN = check_setting_str(CFG, 'Cloudflare', 'auth_domain', censor_log=True)
        CF_POLICY_AUD = check_setting_str(CFG, 'Cloudflare', 'audience_policy', censor_log=True)

        WEB_USE_GZIP = check_setting_bool(CFG, 'General', 'web_use_gzip', True)

        SSL_VERIFY = check_setting_bool(CFG, 'General', 'ssl_verify', True)

        EP_DEFAULT_DELETED_STATUS = check_setting_int(CFG, 'General', 'ep_default_deleted_status', ARCHIVED)
        if EP_DEFAULT_DELETED_STATUS not in (SKIPPED, ARCHIVED, IGNORED):
            EP_DEFAULT_DELETED_STATUS = ARCHIVED

        LAUNCH_BROWSER = check_setting_bool(CFG, 'General', 'launch_browser', True)

        DOWNLOAD_URL = check_setting_str(CFG, 'General', 'download_url')

        LOCALHOST_IP = check_setting_str(CFG, 'General', 'localhost_ip')

        CPU_PRESET = check_setting_str(CFG, 'General', 'cpu_preset', 'NORMAL')

        ANON_REDIRECT = check_setting_str(CFG, 'General', 'anon_redirect', 'http://dereferer.org/?')
        # attempt to help prevent users from breaking links by using a bad url
        if not ANON_REDIRECT.endswith('?'):
            ANON_REDIRECT = ''

        PROXY_SETTING = check_setting_str(CFG, 'General', 'proxy_setting')
        PROXY_INDEXERS = check_setting_bool(CFG, 'General', 'proxy_indexers', True)

        INDEXER_DEFAULT_LANGUAGE = check_setting_str(CFG, 'General', 'indexerDefaultLang', 'en')
        INDEXER_DEFAULT = check_setting_int(CFG, 'General', 'indexer_default', min_val=1, max_val=2, def_val=1)
        INDEXER_TIMEOUT = check_setting_int(CFG, 'General', 'indexer_timeout', 20, min_val=0)

        sickchill.indexer = sickchill.ShowIndexer()

        TVDB_USER = check_setting_str(CFG, 'General', 'tvdb_user')
        TVDB_USER_KEY = check_setting_str(CFG, 'General', 'tvdb_user_key', censor_log=True)

        TRASH_REMOVE_SHOW = check_setting_bool(CFG, 'General', 'trash_remove_show')
        TRASH_ROTATE_LOGS = check_setting_bool(CFG, 'General', 'trash_rotate_logs')

        IGNORE_BROKEN_SYMLINKS = check_setting_bool(CFG, 'General', 'ignore_broken_symlinks')

        SORT_ARTICLE = check_setting_bool(CFG, 'General', 'sort_article')

        API_KEY = check_setting_str(CFG, 'General', 'api_key', censor_log=True)

        ENABLE_HTTPS = check_setting_bool(CFG, 'General', 'enable_https')

        NOTIFY_ON_LOGIN = check_setting_bool(CFG, 'General', 'notify_on_login')

        HTTPS_CERT = check_setting_str(CFG, 'General', 'https_cert', 'server.crt')
        HTTPS_KEY = check_setting_str(CFG, 'General', 'https_key', 'server.key')

        HANDLE_REVERSE_PROXY = check_setting_bool(CFG, 'General', 'handle_reverse_proxy')

        ROOT_DIRS = check_setting_str(CFG, 'General', 'root_dirs')
        if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', ROOT_DIRS):
            ROOT_DIRS = ''

        QUALITY_DEFAULT = check_setting_int(CFG, 'General', 'quality_default', SD)
        QUALITY_ALLOW_HEVC = check_setting_bool(CFG, 'General', 'quality_allow_hevc', False)
        STATUS_DEFAULT = check_setting_int(CFG, 'General', 'status_default', SKIPPED)
        if STATUS_DEFAULT not in (SKIPPED, WANTED, IGNORED):
            STATUS_DEFAULT = SKIPPED
        STATUS_DEFAULT_AFTER = check_setting_int(CFG, 'General', 'status_default_after', WANTED)
        if STATUS_DEFAULT_AFTER not in (SKIPPED, WANTED, IGNORED):
            STATUS_DEFAULT_AFTER = WANTED
        VERSION_NOTIFY = check_setting_bool(CFG, 'General', 'version_notify', True)
        AUTO_UPDATE = check_setting_bool(CFG, 'General', 'auto_update')
        NOTIFY_ON_UPDATE = check_setting_bool(CFG, 'General', 'notify_on_update', True)
        SEASON_FOLDERS_DEFAULT = check_setting_bool(CFG, 'General', 'season_folders_default', True)

        ANIME_DEFAULT = check_setting_bool(CFG, 'General', 'anime_default')
        SCENE_DEFAULT = check_setting_bool(CFG, 'General', 'scene_default')

        PROVIDER_ORDER = check_setting_str(CFG, 'General', 'provider_order').split()

        # TODO: ADD TO MANAGER

        NAMING_PATTERN = check_setting_str(CFG, 'General', 'naming_pattern', 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ABD_PATTERN = check_setting_str(CFG, 'General', 'naming_abd_pattern', '%SN - %A.D - %EN')
        NAMING_CUSTOM_ABD = check_setting_bool(CFG, 'General', 'naming_custom_abd')
        NAMING_SPORTS_PATTERN = check_setting_str(CFG, 'General', 'naming_sports_pattern', '%SN - %A-D - %EN')
        NAMING_ANIME_PATTERN = check_setting_str(CFG, 'General', 'naming_anime_pattern',
                                                 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ANIME = check_setting_int(CFG, 'General', 'naming_anime', 3, min_val=1, max_val=3)
        NAMING_CUSTOM_SPORTS = check_setting_bool(CFG, 'General', 'naming_custom_sports')
        NAMING_CUSTOM_ANIME = check_setting_bool(CFG, 'General', 'naming_custom_anime')
        NAMING_MULTI_EP = check_setting_int(CFG, 'General', 'naming_multi_ep', 1, min_val=1, max_val=max(MULTI_EP_STRINGS))
        NAMING_ANIME_MULTI_EP = check_setting_int(CFG, 'General', 'naming_anime_multi_ep', 1, min_val=1, max_val=max(MULTI_EP_STRINGS))
        NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        NAMING_STRIP_YEAR = check_setting_bool(CFG, 'General', 'naming_strip_year')

        USE_NZBS = check_setting_bool(CFG, 'General', 'use_nzbs', USE_NZBS)
        USE_TORRENTS = check_setting_bool(CFG, 'General', 'use_torrents', USE_TORRENTS)

        NZB_METHOD = check_setting_str(CFG, 'General', 'nzb_method', 'blackhole')
        if NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget', 'download_station'):
            NZB_METHOD = 'blackhole'

        TORRENT_METHOD = check_setting_str(CFG, 'General', 'torrent_method', 'blackhole')

        DOWNLOAD_PROPERS = check_setting_bool(CFG, 'General', 'download_propers', True)
        CHECK_PROPERS_INTERVAL = check_setting_str(CFG, 'General', 'check_propers_interval')
        if CHECK_PROPERS_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            CHECK_PROPERS_INTERVAL = 'daily'

        RANDOMIZE_PROVIDERS = check_setting_bool(CFG, 'General', 'randomize_providers')

        ALLOW_HIGH_PRIORITY = check_setting_bool(CFG, 'General', 'allow_high_priority', True)

        SKIP_REMOVED_FILES = check_setting_bool(CFG, 'General', 'skip_removed_files')

        ALLOWED_EXTENSIONS = check_setting_str(CFG, 'General', 'allowed_extensions', ALLOWED_EXTENSIONS)

        AUTOPOSTPROCESSOR_FREQUENCY = check_setting_int(CFG, 'General', 'autopostprocessor_frequency',
                                                        DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY,
                                                        min_val=MIN_AUTOPOSTPROCESSOR_FREQUENCY, fallback_def=False)

        DAILYSEARCH_FREQUENCY = check_setting_int(CFG, 'General', 'dailysearch_frequency',
                                                  DEFAULT_DAILYSEARCH_FREQUENCY,
                                                  min_val=MIN_DAILYSEARCH_FREQUENCY, fallback_def=False)

        MIN_BACKLOG_FREQUENCY = get_backlog_cycle_time()
        BACKLOG_FREQUENCY = check_setting_int(CFG, 'General', 'backlog_frequency', DEFAULT_BACKLOG_FREQUENCY,
                                              min_val=MIN_BACKLOG_FREQUENCY, fallback_def=False)

        UPDATE_FREQUENCY = check_setting_int(CFG, 'General', 'update_frequency', DEFAULT_UPDATE_FREQUENCY,
                                             min_val=MIN_UPDATE_FREQUENCY, fallback_def=False)

        SHOWUPDATE_HOUR = check_setting_int(CFG, 'General', 'showupdate_hour', DEFAULT_SHOWUPDATE_HOUR,
                                            min_val=0, max_val=23)

        BACKLOG_DAYS = check_setting_int(CFG, 'General', 'backlog_days', 7)

        NEWS_LAST_READ = check_setting_str(CFG, 'General', 'news_last_read', '1970-01-01')
        NEWS_LATEST = NEWS_LAST_READ

        NZB_DIR = check_setting_str(CFG, 'Blackhole', 'nzb_dir')
        TORRENT_DIR = check_setting_str(CFG, 'Blackhole', 'torrent_dir')

        TV_DOWNLOAD_DIR = check_setting_str(CFG, 'General', 'tv_download_dir')
        PROCESS_AUTOMATICALLY = check_setting_bool(CFG, 'General', 'process_automatically')
        NO_DELETE = check_setting_bool(CFG, 'General', 'no_delete')
        USE_ICACLS = check_setting_bool(CFG, 'General', 'use_icacls', True)
        UNPACK = check_setting_int(CFG, 'General', 'unpack', min_val=0, max_val=2)
        UNPACK_DIR = check_setting_str(CFG, 'General', 'unpack_dir')

        config.change_unrar_tool(
            check_setting_str(CFG, 'General', 'unrar_tool', rarfile.UNRAR_TOOL),
            check_setting_str(CFG, 'General', 'alt_unrar_tool', rarfile.ALT_TOOL)
        )

        RENAME_EPISODES = check_setting_bool(CFG, 'General', 'rename_episodes', True)
        AIRDATE_EPISODES = check_setting_bool(CFG, 'General', 'airdate_episodes')
        FILE_TIMESTAMP_TIMEZONE = check_setting_str(CFG, 'General', 'file_timestamp_timezone', 'network')
        KEEP_PROCESSED_DIR = check_setting_bool(CFG, 'General', 'keep_processed_dir', True)
        PROCESS_METHOD = check_setting_str(CFG, 'General', 'process_method', 'copy' if KEEP_PROCESSED_DIR else 'move')
        PROCESSOR_FOLLOW_SYMLINKS = check_setting_bool(CFG, 'General', 'processor_follow_symlinks')
        DELRARCONTENTS = check_setting_bool(CFG, 'General', 'del_rar_contents')
        MOVE_ASSOCIATED_FILES = check_setting_bool(CFG, 'General', 'move_associated_files')
        DELETE_NON_ASSOCIATED_FILES = check_setting_bool(CFG, 'General', 'delete_non_associated_files', True)
        POSTPONE_IF_SYNC_FILES = check_setting_bool(CFG, 'General', 'postpone_if_sync_files', True)
        SYNC_FILES = check_setting_str(CFG, 'General', 'sync_files', SYNC_FILES)
        NFO_RENAME = check_setting_bool(CFG, 'General', 'nfo_rename', True)
        CREATE_MISSING_SHOW_DIRS = check_setting_bool(CFG, 'General', 'create_missing_show_dirs')
        ADD_SHOWS_WO_DIR = check_setting_bool(CFG, 'General', 'add_shows_wo_dir')
        ADD_SHOWS_WITH_YEAR = check_setting_bool(CFG, 'General', 'add_shows_with_year')
        USE_FREE_SPACE_CHECK = check_setting_bool(CFG, 'General', 'use_free_space_check', True)

        USE_SYNOINDEX = check_setting_bool(CFG, 'Synology', 'use_synoindex')

        USE_TRAKT = check_setting_bool(CFG, 'Trakt', 'use_trakt')

        USE_SUBTITLES = check_setting_bool(CFG, 'Subtitles', 'use_subtitles')
        SUBTITLES_INCLUDE_SPECIALS = check_setting_bool(CFG, 'Subtitles', 'subtitles_include_specials', True)
        SUBTITLES_LANGUAGES = check_setting_str(CFG, 'Subtitles', 'subtitles_languages').split(',')
        if SUBTITLES_LANGUAGES[0] == '':
            SUBTITLES_LANGUAGES = []
        SUBTITLES_DIR = check_setting_str(CFG, 'Subtitles', 'subtitles_dir')
        SUBTITLES_SERVICES_LIST = check_setting_str(CFG, 'Subtitles', 'SUBTITLES_SERVICES_LIST').split(',')
        SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                      check_setting_str(CFG, 'Subtitles', 'SUBTITLES_SERVICES_ENABLED').split('|')
                                      if x]
        SUBTITLES_DEFAULT = check_setting_bool(CFG, 'Subtitles', 'subtitles_default')
        SUBTITLES_HISTORY = check_setting_bool(CFG, 'Subtitles', 'subtitles_history')
        SUBTITLES_PERFECT_MATCH = check_setting_bool(CFG, 'Subtitles', 'subtitles_perfect_match', True)
        EMBEDDED_SUBTITLES_ALL = check_setting_bool(CFG, 'Subtitles', 'embedded_subtitles_all')
        SUBTITLES_HEARING_IMPAIRED = check_setting_bool(CFG, 'Subtitles', 'subtitles_hearing_impaired')
        SUBTITLES_FINDER_FREQUENCY = check_setting_int(CFG, 'Subtitles', 'subtitles_finder_frequency', 1, min_val=1)
        SUBTITLES_MULTI = check_setting_bool(CFG, 'Subtitles', 'subtitles_multi', True)
        SUBTITLES_KEEP_ONLY_WANTED = check_setting_bool(CFG, 'Subtitles', 'subtitles_keep_only_wanted')
        SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(CFG, 'Subtitles', 'subtitles_extra_scripts').split('|') if x.strip()]

        ADDIC7ED_USER = check_setting_str(CFG, 'Subtitles', 'addic7ed_username', censor_log=True)
        ADDIC7ED_PASS = check_setting_str(CFG, 'Subtitles', 'addic7ed_password', censor_log=True)

        ITASA_USER = check_setting_str(CFG, 'Subtitles', 'itasa_username', censor_log=True)
        ITASA_PASS = check_setting_str(CFG, 'Subtitles', 'itasa_password', censor_log=True)

        LEGENDASTV_USER = check_setting_str(CFG, 'Subtitles', 'legendastv_username', censor_log=True)
        LEGENDASTV_PASS = check_setting_str(CFG, 'Subtitles', 'legendastv_password', censor_log=True)

        OPENSUBTITLES_USER = check_setting_str(CFG, 'Subtitles', 'opensubtitles_username', censor_log=True)
        OPENSUBTITLES_PASS = check_setting_str(CFG, 'Subtitles', 'opensubtitles_password', censor_log=True)

        SUBSCENTER_USER = check_setting_str(CFG, 'Subtitles', 'subscenter_username', censor_log=True)
        SUBSCENTER_PASS = check_setting_str(CFG, 'Subtitles', 'subscenter_password', censor_log=True)

        USE_FAILED_DOWNLOADS = check_setting_bool(CFG, 'FailedDownloads', 'use_failed_downloads')
        DELETE_FAILED = check_setting_bool(CFG, 'FailedDownloads', 'delete_failed')

        BACKLOG_MISSING_ONLY = check_setting_bool(CFG, 'General', 'backlog_missing_only')

        GIT_PATH = check_setting_str(CFG, 'General', 'git_path')

        IGNORE_WORDS = check_setting_str(CFG, 'General', 'ignore_words', IGNORE_WORDS)
        TRACKERS_LIST = check_setting_str(CFG, 'General', 'trackers_list', TRACKERS_LIST)
        REQUIRE_WORDS = check_setting_str(CFG, 'General', 'require_words', REQUIRE_WORDS)
        PREFER_WORDS = check_setting_str(CFG, 'General', 'prefer_words', PREFER_WORDS)
        IGNORED_SUBS_LIST = check_setting_str(CFG, 'General', 'ignored_subs_list', IGNORED_SUBS_LIST)

        CALENDAR_UNPROTECTED = check_setting_bool(CFG, 'General', 'calendar_unprotected')
        CALENDAR_ICONS = check_setting_bool(CFG, 'General', 'calendar_icons')

        NO_RESTART = check_setting_bool(CFG, 'General', 'no_restart')

        EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(CFG, 'General', 'extra_scripts').split('|') if x.strip()]

        USE_LISTVIEW = check_setting_bool(CFG, 'General', 'use_listview')

        ANIMESUPPORT = False
        USE_ANIDB = check_setting_bool(CFG, 'ANIDB', 'use_anidb')
        ANIDB_USERNAME = check_setting_str(CFG, 'ANIDB', 'anidb_username', censor_log=True)
        ANIDB_PASSWORD = check_setting_str(CFG, 'ANIDB', 'anidb_password', censor_log=True)
        ANIDB_USE_MYLIST = check_setting_bool(CFG, 'ANIDB', 'anidb_use_mylist')

        ANIME_SPLIT_HOME = check_setting_bool(CFG, 'ANIME', 'anime_split_home')
        ANIME_SPLIT_HOME_IN_TABS = check_setting_bool(CFG, 'ANIME', 'anime_split_home_in_tabs')

        HOME_LAYOUT = check_setting_str(CFG, 'GUI', 'home_layout', 'poster')
        HISTORY_LAYOUT = check_setting_str(CFG, 'GUI', 'history_layout', 'detailed')
        HISTORY_LIMIT = check_setting_str(CFG, 'GUI', 'history_limit', '100')
        DISPLAY_SHOW_SPECIALS = check_setting_bool(CFG, 'GUI', 'display_show_specials', True)
        COMING_EPS_LAYOUT = check_setting_str(CFG, 'GUI', 'coming_eps_layout', 'banner')
        COMING_EPS_DISPLAY_PAUSED = check_setting_bool(CFG, 'GUI', 'coming_eps_display_paused')
        COMING_EPS_DISPLAY_SNATCHED = check_setting_bool(CFG, 'GUI', 'coming_eps_display_snatched')
        COMING_EPS_SORT = check_setting_str(CFG, 'GUI', 'coming_eps_sort', 'date')
        COMING_EPS_MISSED_RANGE = check_setting_int(CFG, 'GUI', 'coming_eps_missed_range', 7, min_val=0, max_val=42810, fallback_def=False)
        FUZZY_DATING = check_setting_bool(CFG, 'GUI', 'fuzzy_dating')
        TRIM_ZERO = check_setting_bool(CFG, 'GUI', 'trim_zero')
        DATE_PRESET = check_setting_str(CFG, 'GUI', 'date_preset', '%x')
        TIME_PRESET_W_SECONDS = check_setting_str(CFG, 'GUI', 'time_preset', '%I:%M:%S %p')
        TIME_PRESET = TIME_PRESET_W_SECONDS.replace(":%S", "")
        TIMEZONE_DISPLAY = check_setting_str(CFG, 'GUI', 'timezone_display', 'local')
        POSTER_SORTBY = check_setting_str(CFG, 'GUI', 'poster_sortby', 'name')
        POSTER_SORTDIR = check_setting_int(CFG, 'GUI', 'poster_sortdir', 1, min_val=0, max_val=1)
        DISPLAY_ALL_SEASONS = check_setting_bool(CFG, 'General', 'display_all_seasons', True)
        ENDED_SHOWS_UPDATE_INTERVAL = check_setting_int(CFG, 'General', 'ended_shows_update_interval', 7)

        if check_section(CFG, 'Shares'):
            WINDOWS_SHARES.update(CFG['Shares'])

        if not os.path.isfile(CONFIG_FILE):
            logger.debug("Unable to find '" + CONFIG_FILE + "', all settings will be default!")
            save_config()

        # initialize the main SB database
        main_db_con = db.DBConnection()
        db.upgrade_database(main_db_con, databases.main.InitialSchema)

        # initialize the cache database
        cache_db_con = db.DBConnection('cache.db')
        db.upgrade_database(cache_db_con, databases.cache.InitialSchema)

        # initialize the failed downloads database
        failed_db_con = db.DBConnection('failed.db')
        db.upgrade_database(failed_db_con, databases.failed.InitialSchema)

        # fix up any db problems
        main_db_con = db.DBConnection()
        db.sanity_check_database(main_db_con, databases.main.MainSanityCheck)

        # migrate the config if it needs it
        migrator = ConfigMigrator(CFG)
        migrator.migrate_config()

        # initialize schedulers
        # updaters
        versionCheckScheduler = scheduler.Scheduler(
            versionChecker.CheckVersion(),
            cycleTime=datetime.timedelta(hours=UPDATE_FREQUENCY),
            threadName="CHECKVERSION",
            silent=False
        )

        showQueueScheduler = scheduler.Scheduler(
            show_queue.ShowQueue(),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="SHOWQUEUE"
        )

        showUpdateScheduler = scheduler.Scheduler(
            show_updater.ShowUpdater(),
            run_delay=datetime.timedelta(seconds=20),
            cycleTime=datetime.timedelta(hours=1),
            start_time=datetime.time(hour=SHOWUPDATE_HOUR),
            threadName="SHOWUPDATER",
            silent=False
        )

        # searchers
        searchQueueScheduler = scheduler.Scheduler(
            search_queue.SearchQueue(),
            run_delay=datetime.timedelta(seconds=10),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="SEARCHQUEUE"
        )

        dailySearchScheduler = scheduler.Scheduler(
            dailysearcher.DailySearcher(),
            run_delay=datetime.timedelta(minutes=10),
            cycleTime=datetime.timedelta(minutes=DAILYSEARCH_FREQUENCY),
            threadName="DAILYSEARCHER"
        )

        update_interval = datetime.timedelta(minutes=BACKLOG_FREQUENCY)
        backlogSearchScheduler = searchBacklog.BacklogSearchScheduler(
            searchBacklog.BacklogSearcher(),
            cycleTime=update_interval,
            threadName="BACKLOG",
            run_delay=update_interval
        )

        search_intervals = {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}
        if CHECK_PROPERS_INTERVAL in search_intervals:
            update_interval = datetime.timedelta(minutes=search_intervals[CHECK_PROPERS_INTERVAL])
            run_at = None
        else:
            update_interval = datetime.timedelta(hours=1)
            run_at = datetime.time(hour=1)  # 1 AM

        properFinderScheduler = scheduler.Scheduler(
            properFinder.ProperFinder(),
            cycleTime=update_interval,
            threadName="FINDPROPERS",
            start_time=run_at,
            run_delay=update_interval,
            silent=not DOWNLOAD_PROPERS
        )

        # processors
        postProcessorTaskScheduler = scheduler.Scheduler(
            post_processing_queue.ProcessingQueue(),
            run_delay=datetime.timedelta(seconds=5),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="POSTPROCESSOR",
        )

        autoPostProcessorScheduler = scheduler.Scheduler(
            post_processing_queue.PostProcessor(),
            run_delay=datetime.timedelta(minutes=5),
            cycleTime=datetime.timedelta(minutes=AUTOPOSTPROCESSOR_FREQUENCY),
            threadName="POSTPROCESSOR",
            silent=not PROCESS_AUTOMATICALLY,
        )

        traktCheckerScheduler = scheduler.Scheduler(
            traktChecker.TraktChecker(),
            run_delay=datetime.timedelta(minutes=5),
            cycleTime=datetime.timedelta(hours=1),
            threadName="TRAKTCHECKER",
            silent=not USE_TRAKT
        )

        subtitlesFinderScheduler = scheduler.Scheduler(
            subtitles.SubtitlesFinder(),
            run_delay=datetime.timedelta(minutes=10),
            cycleTime=datetime.timedelta(hours=SUBTITLES_FINDER_FREQUENCY),
            threadName="FINDSUBTITLES",
            silent=not USE_SUBTITLES
        )

        # notifications
        notificationsTaskScheduler = scheduler.Scheduler(
            notifications_queue.NotificationsQueue(),
            run_delay=datetime.timedelta(seconds=5),
            cycleTime=datetime.timedelta(seconds=5),
            threadName="NOTIFICATIONS",
        )

        __INITIALIZED__['0'] = True
        return True


def start():
    with INIT_LOCK:
        if __INITIALIZED__:
            # start sysetm events queue
            events.start()

            # start the daily search scheduler
            dailySearchScheduler.enable = True
            dailySearchScheduler.start()

            # start the backlog scheduler
            backlogSearchScheduler.enable = True
            backlogSearchScheduler.start()

            # start the show updater
            showUpdateScheduler.enable = True
            showUpdateScheduler.start()

            # start the version checker
            versionCheckScheduler.enable = True
            versionCheckScheduler.start()

            # start the queue checker
            showQueueScheduler.enable = True
            showQueueScheduler.start()

            # start the search queue checker
            searchQueueScheduler.enable = True
            searchQueueScheduler.start()

            # start the proper finder
            properFinderScheduler.enable = DOWNLOAD_PROPERS
            properFinderScheduler.start()

            postProcessorTaskScheduler.enable = True
            postProcessorTaskScheduler.start()

            # start the post processor
            autoPostProcessorScheduler.enable = PROCESS_AUTOMATICALLY
            autoPostProcessorScheduler.start()

            # start the subtitles finder
            subtitlesFinderScheduler.enable = USE_SUBTITLES
            subtitlesFinderScheduler.start()

            # # start the trakt checker
            # traktCheckerScheduler.enable = USE_TRAKT
            # traktCheckerScheduler.start()

            notificationsTaskScheduler.enable = True
            notificationsTaskScheduler.start()
            started['0'] = True


def halt():
    with INIT_LOCK:
        if __INITIALIZED__:
            logger.info("Aborting all threads")

            threads = [
                dailySearchScheduler,
                backlogSearchScheduler,
                showUpdateScheduler,
                versionCheckScheduler,
                showQueueScheduler,
                searchQueueScheduler,
                autoPostProcessorScheduler,
                postProcessorTaskScheduler,
                traktCheckerScheduler,
                properFinderScheduler,
                subtitlesFinderScheduler,
                notificationsTaskScheduler,
                events
            ]

            # set them all to stop at the same time
            for t in threads:
                t.stop.set()

            for t in threads:
                logger.info("Waiting for the {0} thread to exit".format(t.name))
                try:
                    t.join(10)
                except Exception:
                    pass

            if ADBA_CONNECTION:
                ADBA_CONNECTION.logout()
                logger.info("Waiting for the ANIDB CONNECTION thread to exit")
                try:
                    ADBA_CONNECTION.join(10)
                except Exception:
                    pass

            __INITIALIZED__.clear()
        started.clear()


def sig_handler(signum=None, frame=None):
    # noinspection PyUnusedLocal
    frame_ = frame
    if not isinstance(signum, type(None)):
        logger.info("Signal {0:d} caught, saving and exiting...".format(int(signum)))
        Shutdown.stop(PID)


def saveAll():
    # write all shows
    logger.info("Saving all shows to the database")
    for show in showList:
        show.saveToDB()

    # save config
    logger.info("Saving config file to disk")
    save_config()


def save_config():
    new_config = ConfigObj(CONFIG_FILE, encoding='UTF-8', indent_type='  ')

    CFG2.write()
    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()

    new_config.update({
        'General': {
            'git_username': GIT_USERNAME,
            'git_token_password': helpers.encrypt(GIT_TOKEN, ENCRYPTION_VERSION),
            'git_reset': int(GIT_RESET),
            'branch': BRANCH,
            'git_remote': GIT_REMOTE,
            'git_remote_url': GIT_REMOTE_URL,
            'cur_commit_hash': CUR_COMMIT_HASH,
            'cur_commit_branch': CUR_COMMIT_BRANCH,
            'config_version': CONFIG_VERSION,
            'encryption_version': int(ENCRYPTION_VERSION),
            'encryption_secret': ENCRYPTION_SECRET,
            'log_nr': int(LOG_NR),
            'log_size': float(LOG_SIZE),
            'socket_timeout': SOCKET_TIMEOUT,
            'web_port': WEB_PORT,
            'web_host': WEB_HOST,
            'web_ipv6': int(WEB_IPV6),
            'web_log': int(WEB_LOG),
            'web_root': WEB_ROOT,
            'web_username': WEB_USERNAME,
            'web_password': helpers.encrypt(WEB_PASSWORD, ENCRYPTION_VERSION),
            'web_cookie_secret': WEB_COOKIE_SECRET,
            'web_use_gzip': int(WEB_USE_GZIP),
            'ssl_verify': int(SSL_VERIFY),
            'download_url': DOWNLOAD_URL,
            'localhost_ip': LOCALHOST_IP,
            'cpu_preset': CPU_PRESET,
            'anon_redirect': ANON_REDIRECT,
            'tvdb_user': TVDB_USER,
            'tvdb_user_key': TVDB_USER_KEY,
            'api_key': API_KEY,
            'debug': int(DEBUG),
            'dbdebug': int(DBDEBUG),
            'default_page': DEFAULT_PAGE,
            'enable_https': int(ENABLE_HTTPS),
            'notify_on_login': int(NOTIFY_ON_LOGIN),
            'https_cert': HTTPS_CERT,
            'https_key': HTTPS_KEY,
            'handle_reverse_proxy': int(HANDLE_REVERSE_PROXY),
            'use_nzbs': int(USE_NZBS),
            'use_torrents': int(USE_TORRENTS),
            'autopostprocessor_frequency': int(AUTOPOSTPROCESSOR_FREQUENCY),
            'dailysearch_frequency': int(DAILYSEARCH_FREQUENCY),
            'backlog_frequency': int(BACKLOG_FREQUENCY),
            'update_frequency': int(UPDATE_FREQUENCY),
            'showupdate_hour': int(SHOWUPDATE_HOUR),
            'download_propers': int(DOWNLOAD_PROPERS),
            'randomize_providers': int(RANDOMIZE_PROVIDERS),
            'check_propers_interval': CHECK_PROPERS_INTERVAL,
            'allow_high_priority': int(ALLOW_HIGH_PRIORITY),
            'skip_removed_files': int(SKIP_REMOVED_FILES),
            'allowed_extensions': ALLOWED_EXTENSIONS,
            'quality_default': int(QUALITY_DEFAULT),
            'quality_allow_hevc': int(QUALITY_ALLOW_HEVC),
            'status_default': int(STATUS_DEFAULT),
            'status_default_after': int(STATUS_DEFAULT_AFTER),
            'season_folders_default': int(SEASON_FOLDERS_DEFAULT),
            'indexer_default': int(INDEXER_DEFAULT),
            'indexer_timeout': int(INDEXER_TIMEOUT),
            'anime_default': int(ANIME_DEFAULT),
            'scene_default': int(SCENE_DEFAULT),
            'provider_order': ' '.join(PROVIDER_ORDER),
            'version_notify': int(VERSION_NOTIFY),
            'auto_update': int(AUTO_UPDATE),
            'notify_on_update': int(NOTIFY_ON_UPDATE),
            'naming_strip_year': int(NAMING_STRIP_YEAR),
            'naming_pattern': NAMING_PATTERN,
            'naming_custom_abd': int(NAMING_CUSTOM_ABD),
            'naming_abd_pattern': NAMING_ABD_PATTERN,
            'naming_custom_sports': int(NAMING_CUSTOM_SPORTS),
            'naming_sports_pattern': NAMING_SPORTS_PATTERN,
            'naming_custom_anime': int(NAMING_CUSTOM_ANIME),
            'naming_anime_pattern': NAMING_ANIME_PATTERN,
            'naming_multi_ep': int(NAMING_MULTI_EP),
            'naming_anime_multi_ep': int(NAMING_ANIME_MULTI_EP),
            'naming_anime': int(NAMING_ANIME),
            'indexerDefaultLang': INDEXER_DEFAULT_LANGUAGE,
            'ep_default_deleted_status': int(EP_DEFAULT_DELETED_STATUS),
            'launch_browser': int(LAUNCH_BROWSER),
            'trash_remove_show': int(TRASH_REMOVE_SHOW),
            'trash_rotate_logs': int(TRASH_ROTATE_LOGS),
            'ignore_broken_symlinks': int(IGNORE_BROKEN_SYMLINKS),
            'sort_article': int(SORT_ARTICLE),
            'proxy_setting': PROXY_SETTING,
            'proxy_indexers': int(PROXY_INDEXERS),
            'use_listview': int(USE_LISTVIEW),

            'backlog_days': int(BACKLOG_DAYS),
            'backlog_missing_only': int(BACKLOG_MISSING_ONLY),

            'root_dirs': ROOT_DIRS if ROOT_DIRS else '',
            'tv_download_dir': TV_DOWNLOAD_DIR,
            'keep_processed_dir': int(KEEP_PROCESSED_DIR),
            'process_method': PROCESS_METHOD,
            'processor_follow_symlinks': int(PROCESSOR_FOLLOW_SYMLINKS),
            'del_rar_contents': int(DELRARCONTENTS),
            'move_associated_files': int(MOVE_ASSOCIATED_FILES),
            'delete_non_associated_files': int(DELETE_NON_ASSOCIATED_FILES),
            'sync_files': SYNC_FILES,
            'postpone_if_sync_files': int(POSTPONE_IF_SYNC_FILES),
            'nfo_rename': int(NFO_RENAME),
            'process_automatically': int(PROCESS_AUTOMATICALLY),
            'no_delete': int(NO_DELETE),
            'use_icacls': int(USE_ICACLS),
            'unpack': int(UNPACK),
            'unpack_dir': UNPACK_DIR,
            'unrar_tool': UNRAR_TOOL,
            'alt_unrar_tool': ALT_UNRAR_TOOL,
            'rename_episodes': int(RENAME_EPISODES),
            'airdate_episodes': int(AIRDATE_EPISODES),
            'file_timestamp_timezone': FILE_TIMESTAMP_TIMEZONE,
            'create_missing_show_dirs': int(CREATE_MISSING_SHOW_DIRS),
            'add_shows_wo_dir': int(ADD_SHOWS_WO_DIR),
            'add_shows_with_year': int(ADD_SHOWS_WITH_YEAR),
            'use_free_space_check': int(USE_FREE_SPACE_CHECK),

            'extra_scripts': '|'.join(EXTRA_SCRIPTS),
            'git_path': GIT_PATH,
            'ignore_words': IGNORE_WORDS,
            'trackers_list': TRACKERS_LIST,
            'require_words': REQUIRE_WORDS,
            'prefer_words': PREFER_WORDS,
            'ignored_subs_list': IGNORED_SUBS_LIST,
            'calendar_unprotected': int(CALENDAR_UNPROTECTED),
            'calendar_icons': int(CALENDAR_ICONS),
            'no_restart': int(NO_RESTART),
            'developer': int(DEVELOPER),
            'display_all_seasons': int(DISPLAY_ALL_SEASONS),
            'ended_shows_update_interval': int(ENDED_SHOWS_UPDATE_INTERVAL),
            'news_last_read': NEWS_LAST_READ,
        },
        'Cloudflare': {
            'auth_domain': CF_AUTH_DOMAIN,
            'audience_policy': CF_POLICY_AUD
        },

        'Shares': WINDOWS_SHARES,
        'GUI': {
            'gui_name': GUI_NAME,
            'language': GUI_LANG,
            'theme_name': THEME_NAME,
            'sickchill_background': int(SICKCHILL_BACKGROUND),
            'sickchill_background_path': SICKCHILL_BACKGROUND_PATH,
            'fanart_background': int(FANART_BACKGROUND),
            'fanart_background_opacity': FANART_BACKGROUND_OPACITY,
            'custom_css': int(CUSTOM_CSS),
            'custom_css_path': CUSTOM_CSS_PATH,
            'home_layout': HOME_LAYOUT,
            'history_layout': HISTORY_LAYOUT,
            'history_limit': HISTORY_LIMIT,
            'display_show_specials': int(DISPLAY_SHOW_SPECIALS),
            'coming_eps_layout': COMING_EPS_LAYOUT,
            'coming_eps_display_paused': int(COMING_EPS_DISPLAY_PAUSED),
            'coming_eps_display_snatched': int(COMING_EPS_DISPLAY_SNATCHED),
            'coming_eps_sort': COMING_EPS_SORT,
            'coming_eps_missed_range': config.min_max(COMING_EPS_MISSED_RANGE, 7, 0, 42810),
            'fuzzy_dating': int(FUZZY_DATING),
            'trim_zero': int(TRIM_ZERO),
            'date_preset': DATE_PRESET,
            'time_preset': TIME_PRESET_W_SECONDS,
            'timezone_display': TIMEZONE_DISPLAY,
            'poster_sortby': POSTER_SORTBY,
            'poster_sortdir': POSTER_SORTDIR
        },

        'Subtitles': {
            'use_subtitles': int(USE_SUBTITLES),
            'subtitles_include_specials': int(SUBTITLES_INCLUDE_SPECIALS),
            'subtitles_languages': ','.join(SUBTITLES_LANGUAGES),
            'SUBTITLES_SERVICES_LIST': ','.join(SUBTITLES_SERVICES_LIST),
            'SUBTITLES_SERVICES_ENABLED': '|'.join([str(x) for x in SUBTITLES_SERVICES_ENABLED]),
            'subtitles_dir': SUBTITLES_DIR,
            'subtitles_default': int(SUBTITLES_DEFAULT),
            'subtitles_history': int(SUBTITLES_HISTORY),
            'subtitles_perfect_match': int(SUBTITLES_PERFECT_MATCH),
            'embedded_subtitles_all': int(EMBEDDED_SUBTITLES_ALL),
            'subtitles_hearing_impaired': int(SUBTITLES_HEARING_IMPAIRED),
            'subtitles_finder_frequency': int(SUBTITLES_FINDER_FREQUENCY),
            'subtitles_multi': int(SUBTITLES_MULTI),
            'subtitles_extra_scripts': '|'.join(SUBTITLES_EXTRA_SCRIPTS),
            'subtitles_keep_only_wanted': int(SUBTITLES_KEEP_ONLY_WANTED),
        },

        'FailedDownloads': {
            'use_failed_downloads': int(USE_FAILED_DOWNLOADS),
            'delete_failed': int(DELETE_FAILED),
        },

        'ANIDB': {
            'use_anidb': int(USE_ANIDB),
            'anidb_username': ANIDB_USERNAME,
            'anidb_password': helpers.encrypt(ANIDB_PASSWORD, ENCRYPTION_VERSION),
            'anidb_use_mylist': int(ANIDB_USE_MYLIST),
        },

        'ANIME': {
            'anime_split_home': int(ANIME_SPLIT_HOME),
            'anime_split_home_in_tabs': int(ANIME_SPLIT_HOME_IN_TABS),
        }
    })
    new_config.write()


def launchBrowser(protocol='http', startPort=None, web_root='/'):

    try:
        # Stdlib Imports
        import webbrowser
    except ImportError:
        logger.warning("Unable to load the webbrowser module, cannot launch the browser.")
        return

    if not startPort:
        startPort = WEB_PORT

    browserURL = '{0}://localhost:{1:d}{2}/home/'.format(protocol, startPort, web_root)

    try:
        webbrowser.open(browserURL, 2, 1)
    except Exception:
        try:
            webbrowser.open(browserURL, 1, 1)
        except Exception:
            logger.exception("Unable to launch a browser")
