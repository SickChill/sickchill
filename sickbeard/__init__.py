# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.


import webbrowser
import datetime
import socket
import os
import re
import os.path
import shutil
import shutil_custom

shutil.copyfile = shutil_custom.copyfile_custom

from threading import Lock
import sys

from github import Github

from sickbeard import metadata
from sickbeard import providers
from sickbeard.providers.generic import GenericProvider
from sickbeard.config import CheckSection, check_setting_int, check_setting_str, check_setting_float, ConfigMigrator, \
    naming_ep_type
from sickbeard import searchBacklog, showUpdater, versionChecker, properFinder, autoPostProcesser, \
    subtitles, traktChecker
from sickbeard import db
from sickbeard import helpers
from sickbeard import scheduler
from sickbeard import search_queue
from sickbeard import show_queue
from sickbeard import logger
from sickbeard import naming
from sickbeard import dailysearcher
from sickbeard.indexers import indexer_api
from sickbeard.indexers.indexer_exceptions import indexer_shownotfound, indexer_showincomplete, indexer_exception, indexer_error, \
    indexer_episodenotfound, indexer_attributenotfound, indexer_seasonnotfound, indexer_userabort, indexerExcepts
from sickbeard.common import SD
from sickbeard.common import SKIPPED
from sickbeard.common import WANTED
from sickbeard.databases import mainDB, cache_db, failed_db
from sickrage.helper.exceptions import ex
from sickrage.system.Shutdown import Shutdown

from configobj import ConfigObj

import requests
requests.packages.urllib3.disable_warnings()

indexerApi = indexer_api.indexerApi

PID = None

CFG = None
CONFIG_FILE = None

# This is the version of the config we EXPECT to find
CONFIG_VERSION = 7

# Default encryption version (0 for None)
ENCRYPTION_VERSION = 0
ENCRYPTION_SECRET = None

PROG_DIR = '.'
MY_FULLNAME = None
MY_NAME = None
MY_ARGS = []
SYS_ENCODING = ''
DATA_DIR = ''
CREATEPID = False
PIDFILE = ''

DAEMON = None
NO_RESIZE = False

# system events
events = None

# github
gh = None

# schedualers
dailySearchScheduler = None
backlogSearchScheduler = None
showUpdateScheduler = None
versionCheckScheduler = None
showQueueScheduler = None
searchQueueScheduler = None
properFinderScheduler = None
autoPostProcesserScheduler = None
subtitlesFinderScheduler = None
traktCheckerScheduler = None

showList = None
loadingShowList = None

providerList = []
newznabProviderList = []
torrentRssProviderList = []
metadata_provider_dict = {}

NEWEST_VERSION = None
NEWEST_VERSION_STRING = None
VERSION_NOTIFY = False
AUTO_UPDATE = False
NOTIFY_ON_UPDATE = False
CUR_COMMIT_HASH = None
BRANCH = ''

GIT_RESET = True
GIT_REMOTE = ''
GIT_REMOTE_URL = ''
CUR_COMMIT_BRANCH = ''
GIT_ORG = 'SiCKRAGETV'
GIT_REPO = 'SickRage'
GIT_USERNAME = None
GIT_PASSWORD = None
GIT_PATH = None
GIT_AUTOISSUES = False
GIT_NEWVER = False
DEVELOPER = False

NEWS_URL = 'http://sickragetv.github.io/sickrage-news/news.md'
NEWS_LAST_READ = None
NEWS_LATEST = None
NEWS_UNREAD = 0

INIT_LOCK = Lock()
started = False

ACTUAL_LOG_DIR = None
LOG_DIR = None
LOG_NR = 5
LOG_SIZE = 1048576

SOCKET_TIMEOUT = None

WEB_PORT = None
WEB_LOG = None
WEB_ROOT = None
WEB_USERNAME = None
WEB_PASSWORD = None
WEB_HOST = None
WEB_IPV6 = None
WEB_COOKIE_SECRET = None
WEB_USE_GZIP = True

DOWNLOAD_URL = None

HANDLE_REVERSE_PROXY = False
PROXY_SETTING = None
PROXY_INDEXERS = True
SSL_VERIFY = True

LOCALHOST_IP = None

CPU_PRESET = None

ANON_REDIRECT = None

API_KEY = None
API_ROOT = None

ENABLE_HTTPS = False
HTTPS_CERT = None
HTTPS_KEY = None

INDEXER_DEFAULT_LANGUAGE = None
EP_DEFAULT_DELETED_STATUS = None
LAUNCH_BROWSER = False
CACHE_DIR = None
ACTUAL_CACHE_DIR = None
ROOT_DIRS = None

TRASH_REMOVE_SHOW = False
TRASH_ROTATE_LOGS = False
SORT_ARTICLE = False
DEBUG = False
DISPLAY_ALL_SEASONS = True
DEFAULT_PAGE = 'home'


USE_LISTVIEW = False
METADATA_KODI = None
METADATA_KODI_12PLUS = None
METADATA_MEDIABROWSER = None
METADATA_PS3 = None
METADATA_WDTV = None
METADATA_TIVO = None
METADATA_MEDE8ER = None

QUALITY_DEFAULT = None
STATUS_DEFAULT = None
STATUS_DEFAULT_AFTER = None
FLATTEN_FOLDERS_DEFAULT = False
SUBTITLES_DEFAULT = False
INDEXER_DEFAULT = None
INDEXER_TIMEOUT = None
SCENE_DEFAULT = False
ANIME_DEFAULT = False
ARCHIVE_DEFAULT = False
PROVIDER_ORDER = []

NAMING_MULTI_EP = False
NAMING_ANIME_MULTI_EP = False
NAMING_PATTERN = None
NAMING_ABD_PATTERN = None
NAMING_CUSTOM_ABD = False
NAMING_SPORTS_PATTERN = None
NAMING_CUSTOM_SPORTS = False
NAMING_ANIME_PATTERN = None
NAMING_CUSTOM_ANIME = False
NAMING_FORCE_FOLDERS = False
NAMING_STRIP_YEAR = False
NAMING_ANIME = None

USE_NZBS = False
USE_TORRENTS = False

NZB_METHOD = None
NZB_DIR = None
USENET_RETENTION = None
TORRENT_METHOD = None
TORRENT_DIR = None
DOWNLOAD_PROPERS = False
CHECK_PROPERS_INTERVAL = None
ALLOW_HIGH_PRIORITY = False
SAB_FORCED = False
RANDOMIZE_PROVIDERS = False

AUTOPOSTPROCESSER_FREQUENCY = None
DAILYSEARCH_FREQUENCY = None
UPDATE_FREQUENCY = None
BACKLOG_FREQUENCY = None
SHOWUPDATE_HOUR = None

DEFAULT_AUTOPOSTPROCESSER_FREQUENCY = 10
DEFAULT_DAILYSEARCH_FREQUENCY = 40
DEFAULT_BACKLOG_FREQUENCY = 21
DEFAULT_UPDATE_FREQUENCY = 1
DEFAULT_SHOWUPDATE_HOUR = 3

MIN_AUTOPOSTPROCESSER_FREQUENCY = 1
MIN_DAILYSEARCH_FREQUENCY = 10
MIN_BACKLOG_FREQUENCY = 10
MIN_UPDATE_FREQUENCY = 1

BACKLOG_DAYS = 7

ADD_SHOWS_WO_DIR = False
CREATE_MISSING_SHOW_DIRS = False
RENAME_EPISODES = False
AIRDATE_EPISODES = False
FILE_TIMESTAMP_TIMEZONE = None
PROCESS_AUTOMATICALLY = False
NO_DELETE = False
KEEP_PROCESSED_DIR = False
PROCESS_METHOD = None
DELRARCONTENTS = False
MOVE_ASSOCIATED_FILES = False
POSTPONE_IF_SYNC_FILES = True
NFO_RENAME = True
TV_DOWNLOAD_DIR = None
UNPACK = False
SKIP_REMOVED_FILES = False

NZBS = False
NZBS_UID = None
NZBS_HASH = None

OMGWTFNZBS = False
OMGWTFNZBS_USERNAME = None
OMGWTFNZBS_APIKEY = None

NEWZBIN = False
NEWZBIN_USERNAME = None
NEWZBIN_PASSWORD = None

SAB_USERNAME = None
SAB_PASSWORD = None
SAB_APIKEY = None
SAB_CATEGORY = None
SAB_CATEGORY_BACKLOG = None
SAB_CATEGORY_ANIME = None
SAB_CATEGORY_ANIME_BACKLOG = None
SAB_HOST = ''

NZBGET_USERNAME = None
NZBGET_PASSWORD = None
NZBGET_CATEGORY = None
NZBGET_CATEGORY_BACKLOG = None
NZBGET_CATEGORY_ANIME = None
NZBGET_CATEGORY_ANIME_BACKLOG = None
NZBGET_HOST = None
NZBGET_USE_HTTPS = False
NZBGET_PRIORITY = 100

TORRENT_USERNAME = None
TORRENT_PASSWORD = None
TORRENT_HOST = ''
TORRENT_PATH = ''
TORRENT_SEED_TIME = None
TORRENT_PAUSED = False
TORRENT_HIGH_BANDWIDTH = False
TORRENT_LABEL = ''
TORRENT_LABEL_ANIME = ''
TORRENT_VERIFY_CERT = False
TORRENT_RPCURL = 'transmission'
TORRENT_AUTH_TYPE = 'none'

USE_KODI = False
KODI_ALWAYS_ON = True
KODI_NOTIFY_ONSNATCH = False
KODI_NOTIFY_ONDOWNLOAD = False
KODI_NOTIFY_ONSUBTITLEDOWNLOAD = False
KODI_UPDATE_LIBRARY = False
KODI_UPDATE_FULL = False
KODI_UPDATE_ONLYFIRST = False
KODI_HOST = ''
KODI_USERNAME = None
KODI_PASSWORD = None

USE_PLEX = False
PLEX_NOTIFY_ONSNATCH = False
PLEX_NOTIFY_ONDOWNLOAD = False
PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = False
PLEX_UPDATE_LIBRARY = False
PLEX_SERVER_HOST = None
PLEX_SERVER_TOKEN = None
PLEX_HOST = None
PLEX_USERNAME = None
PLEX_PASSWORD = None
USE_PLEX_CLIENT = False
PLEX_CLIENT_USERNAME = None
PLEX_CLIENT_PASSWORD = None

USE_EMBY = False
EMBY_HOST = None
EMBY_APIKEY = None

USE_GROWL = False
GROWL_NOTIFY_ONSNATCH = False
GROWL_NOTIFY_ONDOWNLOAD = False
GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
GROWL_HOST = ''
GROWL_PASSWORD = None

USE_FREEMOBILE = False
FREEMOBILE_NOTIFY_ONSNATCH = False
FREEMOBILE_NOTIFY_ONDOWNLOAD = False
FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = False
FREEMOBILE_ID = ''
FREEMOBILE_APIKEY = ''

USE_PROWL = False
PROWL_NOTIFY_ONSNATCH = False
PROWL_NOTIFY_ONDOWNLOAD = False
PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
PROWL_API = None
PROWL_PRIORITY = 0

USE_TWITTER = False
TWITTER_NOTIFY_ONSNATCH = False
TWITTER_NOTIFY_ONDOWNLOAD = False
TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = False
TWITTER_USERNAME = None
TWITTER_PASSWORD = None
TWITTER_PREFIX = None
TWITTER_DMTO = None
TWITTER_USEDM = False

USE_BOXCAR = False
BOXCAR_NOTIFY_ONSNATCH = False
BOXCAR_NOTIFY_ONDOWNLOAD = False
BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = False
BOXCAR_USERNAME = None
BOXCAR_PASSWORD = None
BOXCAR_PREFIX = None

USE_BOXCAR2 = False
BOXCAR2_NOTIFY_ONSNATCH = False
BOXCAR2_NOTIFY_ONDOWNLOAD = False
BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = False
BOXCAR2_ACCESSTOKEN = None

USE_PUSHOVER = False
PUSHOVER_NOTIFY_ONSNATCH = False
PUSHOVER_NOTIFY_ONDOWNLOAD = False
PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHOVER_USERKEY = None
PUSHOVER_APIKEY = None
PUSHOVER_DEVICE = None
PUSHOVER_SOUND = None

USE_LIBNOTIFY = False
LIBNOTIFY_NOTIFY_ONSNATCH = False
LIBNOTIFY_NOTIFY_ONDOWNLOAD = False
LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = False

USE_NMJ = False
NMJ_HOST = None
NMJ_DATABASE = None
NMJ_MOUNT = None

ANIMESUPPORT = False
USE_ANIDB = False
ANIDB_USERNAME = None
ANIDB_PASSWORD = None
ANIDB_USE_MYLIST = False
ADBA_CONNECTION = None
ANIME_SPLIT_HOME = False

USE_SYNOINDEX = False

USE_NMJv2 = False
NMJv2_HOST = None
NMJv2_DATABASE = None
NMJv2_DBLOC = None

USE_SYNOLOGYNOTIFIER = False
SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = False
SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = False
SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = False

USE_TRAKT = False
TRAKT_USERNAME = None
TRAKT_ACCESS_TOKEN = None
TRAKT_REFRESH_TOKEN = None
TRAKT_REMOVE_WATCHLIST = False
TRAKT_REMOVE_SERIESLIST = False
TRAKT_REMOVE_SHOW_FROM_SICKRAGE = False
TRAKT_SYNC_WATCHLIST = False
TRAKT_METHOD_ADD = None
TRAKT_START_PAUSED = False
TRAKT_USE_RECOMMENDED = False
TRAKT_SYNC = False
TRAKT_SYNC_REMOVE = False
TRAKT_DEFAULT_INDEXER = None
TRAKT_TIMEOUT = None
TRAKT_BLACKLIST_NAME = None

USE_PYTIVO = False
PYTIVO_NOTIFY_ONSNATCH = False
PYTIVO_NOTIFY_ONDOWNLOAD = False
PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = False
PYTIVO_UPDATE_LIBRARY = False
PYTIVO_HOST = ''
PYTIVO_SHARE_NAME = ''
PYTIVO_TIVO_NAME = ''

USE_NMA = False
NMA_NOTIFY_ONSNATCH = False
NMA_NOTIFY_ONDOWNLOAD = False
NMA_NOTIFY_ONSUBTITLEDOWNLOAD = False
NMA_API = None
NMA_PRIORITY = 0

USE_PUSHALOT = False
PUSHALOT_NOTIFY_ONSNATCH = False
PUSHALOT_NOTIFY_ONDOWNLOAD = False
PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHALOT_AUTHORIZATIONTOKEN = None

USE_PUSHBULLET = False
PUSHBULLET_NOTIFY_ONSNATCH = False
PUSHBULLET_NOTIFY_ONDOWNLOAD = False
PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = False
PUSHBULLET_API = None
PUSHBULLET_DEVICE = None

USE_EMAIL = False
EMAIL_NOTIFY_ONSNATCH = False
EMAIL_NOTIFY_ONDOWNLOAD = False
EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = False
EMAIL_HOST = None
EMAIL_PORT = 25
EMAIL_TLS = False
EMAIL_USER = None
EMAIL_PASSWORD = None
EMAIL_FROM = None
EMAIL_LIST = None

GUI_NAME = None
HOME_LAYOUT = None
HISTORY_LAYOUT = None
HISTORY_LIMIT = 0
DISPLAY_SHOW_SPECIALS = False
COMING_EPS_LAYOUT = None
COMING_EPS_DISPLAY_PAUSED = False
COMING_EPS_SORT = None
COMING_EPS_MISSED_RANGE = None
FUZZY_DATING = False
TRIM_ZERO = False
DATE_PRESET = None
TIME_PRESET = None
TIME_PRESET_W_SECONDS = None
TIMEZONE_DISPLAY = None
THEME_NAME = None
POSTER_SORTBY = None
POSTER_SORTDIR = None
FILTER_ROW = True

USE_SUBTITLES = False
SUBTITLES_LANGUAGES = []
SUBTITLES_DIR = ''
SUBTITLES_SERVICES_LIST = []
SUBTITLES_SERVICES_ENABLED = []
SUBTITLES_HISTORY = False
EMBEDDED_SUBTITLES_ALL = False
SUBTITLES_HEARING_IMPAIRED = False
SUBTITLES_FINDER_FREQUENCY = 1
SUBTITLES_MULTI = False
SUBTITLES_EXTRA_SCRIPTS = []

ADDIC7ED_USER = None
ADDIC7ED_PASS = None

OPENSUBTITLES_USER = None
OPENSUBTITLES_PASS = None

LEGENDASTV_USER = None
LEGENDASTV_PASS = None

USE_FAILED_DOWNLOADS = False
DELETE_FAILED = False

EXTRA_SCRIPTS = []

IGNORE_WORDS = "german,french,core2hd,dutch,swedish,reenc,MrLss"
REQUIRE_WORDS = ""
IGNORED_SUBS_LIST = "dk,fin,heb,kor,nor,nordic,pl,swe"
SYNC_FILES = "!sync,lftp-pget-status,part,bts,!qb"

CALENDAR_UNPROTECTED = False
CALENDAR_ICONS = False
NO_RESTART = False

TMDB_API_KEY = 'edc5f123313769de83a71e157758030b'
# TRAKT_API_KEY = 'd4161a7a106424551add171e5470112e4afdaf2438e6ef2fe0548edc75924868'

TRAKT_API_KEY = '5c65f55e11d48c35385d9e8670615763a605fad28374c8ae553a7b7a50651ddd'
TRAKT_API_SECRET = 'b53e32045ac122a445ef163e6d859403301ffe9b17fb8321d428531b69022a82'
TRAKT_PIN_URL = 'https://trakt.tv/pin/4562'
TRAKT_OAUTH_URL = 'https://trakt.tv/'
TRAKT_API_URL = 'https://api-v2launch.trakt.tv/'

FANART_API_KEY = '9b3afaf26f6241bdb57d6cc6bd798da7'

SHOWS_RECENT = []

__INITIALIZED__ = False

NEWZNAB_DATA = None

def get_backlog_cycle_time():
    cycletime = DAILYSEARCH_FREQUENCY * 2 + 7
    return max([cycletime, 720])


def initialize(consoleLogging=True):
    with INIT_LOCK:

        global BRANCH, GIT_RESET, GIT_REMOTE, GIT_REMOTE_URL, CUR_COMMIT_HASH, CUR_COMMIT_BRANCH, GIT_NEWVER, ACTUAL_LOG_DIR, LOG_DIR, LOG_NR, LOG_SIZE, WEB_PORT, WEB_LOG, ENCRYPTION_VERSION, ENCRYPTION_SECRET, WEB_ROOT, WEB_USERNAME, WEB_PASSWORD, WEB_HOST, WEB_IPV6, WEB_COOKIE_SECRET, WEB_USE_GZIP, API_KEY, ENABLE_HTTPS, HTTPS_CERT, HTTPS_KEY, \
            HANDLE_REVERSE_PROXY, USE_NZBS, USE_TORRENTS, NZB_METHOD, NZB_DIR, DOWNLOAD_PROPERS, RANDOMIZE_PROVIDERS, CHECK_PROPERS_INTERVAL, ALLOW_HIGH_PRIORITY, SAB_FORCED, TORRENT_METHOD, \
            SAB_USERNAME, SAB_PASSWORD, SAB_APIKEY, SAB_CATEGORY, SAB_CATEGORY_BACKLOG, SAB_CATEGORY_ANIME, SAB_CATEGORY_ANIME_BACKLOG, SAB_HOST, \
            NZBGET_USERNAME, NZBGET_PASSWORD, NZBGET_CATEGORY, NZBGET_CATEGORY_BACKLOG, NZBGET_CATEGORY_ANIME, NZBGET_CATEGORY_ANIME_BACKLOG, NZBGET_PRIORITY, NZBGET_HOST, NZBGET_USE_HTTPS, backlogSearchScheduler, \
            TORRENT_USERNAME, TORRENT_PASSWORD, TORRENT_HOST, TORRENT_PATH, TORRENT_SEED_TIME, TORRENT_PAUSED, TORRENT_HIGH_BANDWIDTH, TORRENT_LABEL, TORRENT_LABEL_ANIME, TORRENT_VERIFY_CERT, TORRENT_RPCURL, TORRENT_AUTH_TYPE, \
            USE_KODI, KODI_ALWAYS_ON, KODI_NOTIFY_ONSNATCH, KODI_NOTIFY_ONDOWNLOAD, KODI_NOTIFY_ONSUBTITLEDOWNLOAD, KODI_UPDATE_FULL, KODI_UPDATE_ONLYFIRST, \
            KODI_UPDATE_LIBRARY, KODI_HOST, KODI_USERNAME, KODI_PASSWORD, BACKLOG_FREQUENCY, \
            USE_TRAKT, TRAKT_USERNAME, TRAKT_ACCESS_TOKEN, TRAKT_REFRESH_TOKEN, TRAKT_REMOVE_WATCHLIST, TRAKT_SYNC_WATCHLIST, TRAKT_REMOVE_SHOW_FROM_SICKRAGE, TRAKT_METHOD_ADD, TRAKT_START_PAUSED, traktCheckerScheduler, TRAKT_USE_RECOMMENDED, TRAKT_SYNC, TRAKT_SYNC_REMOVE, TRAKT_DEFAULT_INDEXER, TRAKT_REMOVE_SERIESLIST, TRAKT_TIMEOUT, TRAKT_BLACKLIST_NAME, \
            USE_PLEX, PLEX_NOTIFY_ONSNATCH, PLEX_NOTIFY_ONDOWNLOAD, PLEX_NOTIFY_ONSUBTITLEDOWNLOAD, PLEX_UPDATE_LIBRARY, USE_PLEX_CLIENT, PLEX_CLIENT_USERNAME, PLEX_CLIENT_PASSWORD, \
            PLEX_SERVER_HOST, PLEX_SERVER_TOKEN, PLEX_HOST, PLEX_USERNAME, PLEX_PASSWORD, MIN_BACKLOG_FREQUENCY, SKIP_REMOVED_FILES, \
            USE_EMBY, EMBY_HOST, EMBY_APIKEY, \
            showUpdateScheduler, __INITIALIZED__, INDEXER_DEFAULT_LANGUAGE, EP_DEFAULT_DELETED_STATUS, LAUNCH_BROWSER, TRASH_REMOVE_SHOW, TRASH_ROTATE_LOGS, SORT_ARTICLE, showList, loadingShowList, \
            NEWZNAB_DATA, NZBS, NZBS_UID, NZBS_HASH, INDEXER_DEFAULT, INDEXER_TIMEOUT, USENET_RETENTION, TORRENT_DIR, \
            QUALITY_DEFAULT, FLATTEN_FOLDERS_DEFAULT, SUBTITLES_DEFAULT, STATUS_DEFAULT, STATUS_DEFAULT_AFTER, \
            GROWL_NOTIFY_ONSNATCH, GROWL_NOTIFY_ONDOWNLOAD, GROWL_NOTIFY_ONSUBTITLEDOWNLOAD, TWITTER_NOTIFY_ONSNATCH, TWITTER_NOTIFY_ONDOWNLOAD, TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD, USE_FREEMOBILE, FREEMOBILE_ID, FREEMOBILE_APIKEY, FREEMOBILE_NOTIFY_ONSNATCH, FREEMOBILE_NOTIFY_ONDOWNLOAD, FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_GROWL, GROWL_HOST, GROWL_PASSWORD, USE_PROWL, PROWL_NOTIFY_ONSNATCH, PROWL_NOTIFY_ONDOWNLOAD, PROWL_NOTIFY_ONSUBTITLEDOWNLOAD, PROWL_API, PROWL_PRIORITY, \
            USE_PYTIVO, PYTIVO_NOTIFY_ONSNATCH, PYTIVO_NOTIFY_ONDOWNLOAD, PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD, PYTIVO_UPDATE_LIBRARY, PYTIVO_HOST, PYTIVO_SHARE_NAME, PYTIVO_TIVO_NAME, \
            USE_NMA, NMA_NOTIFY_ONSNATCH, NMA_NOTIFY_ONDOWNLOAD, NMA_NOTIFY_ONSUBTITLEDOWNLOAD, NMA_API, NMA_PRIORITY, \
            USE_PUSHALOT, PUSHALOT_NOTIFY_ONSNATCH, PUSHALOT_NOTIFY_ONDOWNLOAD, PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHALOT_AUTHORIZATIONTOKEN, \
            USE_PUSHBULLET, PUSHBULLET_NOTIFY_ONSNATCH, PUSHBULLET_NOTIFY_ONDOWNLOAD, PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHBULLET_API, PUSHBULLET_DEVICE, \
            versionCheckScheduler, VERSION_NOTIFY, AUTO_UPDATE, NOTIFY_ON_UPDATE, PROCESS_AUTOMATICALLY, NO_DELETE, UNPACK, CPU_PRESET, \
            KEEP_PROCESSED_DIR, PROCESS_METHOD, DELRARCONTENTS, TV_DOWNLOAD_DIR, UPDATE_FREQUENCY, \
            showQueueScheduler, searchQueueScheduler, ROOT_DIRS, CACHE_DIR, ACTUAL_CACHE_DIR, TIMEZONE_DISPLAY, \
            NAMING_PATTERN, NAMING_MULTI_EP, NAMING_ANIME_MULTI_EP, NAMING_FORCE_FOLDERS, NAMING_ABD_PATTERN, NAMING_CUSTOM_ABD, NAMING_SPORTS_PATTERN, NAMING_CUSTOM_SPORTS, NAMING_ANIME_PATTERN, NAMING_CUSTOM_ANIME, NAMING_STRIP_YEAR, \
            RENAME_EPISODES, AIRDATE_EPISODES, FILE_TIMESTAMP_TIMEZONE, properFinderScheduler, PROVIDER_ORDER, autoPostProcesserScheduler, \
            providerList, newznabProviderList, torrentRssProviderList, \
            EXTRA_SCRIPTS, USE_TWITTER, TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_PREFIX, DAILYSEARCH_FREQUENCY, TWITTER_DMTO, TWITTER_USEDM, \
            USE_BOXCAR, BOXCAR_USERNAME, BOXCAR_NOTIFY_ONDOWNLOAD, BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD, BOXCAR_NOTIFY_ONSNATCH, \
            USE_BOXCAR2, BOXCAR2_ACCESSTOKEN, BOXCAR2_NOTIFY_ONDOWNLOAD, BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD, BOXCAR2_NOTIFY_ONSNATCH, \
            USE_PUSHOVER, PUSHOVER_USERKEY, PUSHOVER_APIKEY, PUSHOVER_DEVICE, PUSHOVER_NOTIFY_ONDOWNLOAD, PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHOVER_NOTIFY_ONSNATCH, PUSHOVER_SOUND, \
            USE_LIBNOTIFY, LIBNOTIFY_NOTIFY_ONSNATCH, LIBNOTIFY_NOTIFY_ONDOWNLOAD, LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD, USE_NMJ, NMJ_HOST, NMJ_DATABASE, NMJ_MOUNT, USE_NMJv2, NMJv2_HOST, NMJv2_DATABASE, NMJv2_DBLOC, USE_SYNOINDEX, \
            USE_SYNOLOGYNOTIFIER, SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH, SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD, SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_TLS, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_NOTIFY_ONSNATCH, EMAIL_NOTIFY_ONDOWNLOAD, EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD, EMAIL_LIST, \
            USE_LISTVIEW, METADATA_KODI, METADATA_KODI_12PLUS, METADATA_MEDIABROWSER, METADATA_PS3, metadata_provider_dict, \
            NEWZBIN, NEWZBIN_USERNAME, NEWZBIN_PASSWORD, GIT_PATH, MOVE_ASSOCIATED_FILES, SYNC_FILES, POSTPONE_IF_SYNC_FILES, dailySearchScheduler, NFO_RENAME, \
            GUI_NAME, HOME_LAYOUT, HISTORY_LAYOUT, DISPLAY_SHOW_SPECIALS, COMING_EPS_LAYOUT, COMING_EPS_SORT, COMING_EPS_DISPLAY_PAUSED, COMING_EPS_MISSED_RANGE, FUZZY_DATING, TRIM_ZERO, DATE_PRESET, TIME_PRESET, TIME_PRESET_W_SECONDS, THEME_NAME, FILTER_ROW, \
            POSTER_SORTBY, POSTER_SORTDIR, HISTORY_LIMIT, CREATE_MISSING_SHOW_DIRS, ADD_SHOWS_WO_DIR, \
            METADATA_WDTV, METADATA_TIVO, METADATA_MEDE8ER, IGNORE_WORDS, IGNORED_SUBS_LIST, REQUIRE_WORDS, CALENDAR_UNPROTECTED, CALENDAR_ICONS, NO_RESTART, \
            USE_SUBTITLES, SUBTITLES_LANGUAGES, SUBTITLES_DIR, SUBTITLES_SERVICES_LIST, SUBTITLES_SERVICES_ENABLED, SUBTITLES_HISTORY, SUBTITLES_FINDER_FREQUENCY, SUBTITLES_MULTI, EMBEDDED_SUBTITLES_ALL, SUBTITLES_EXTRA_SCRIPTS, subtitlesFinderScheduler, \
            SUBTITLES_HEARING_IMPAIRED, ADDIC7ED_USER, ADDIC7ED_PASS, LEGENDASTV_USER, LEGENDASTV_PASS, OPENSUBTITLES_USER, OPENSUBTITLES_PASS, \
            USE_FAILED_DOWNLOADS, DELETE_FAILED, ANON_REDIRECT, LOCALHOST_IP, DEBUG, DEFAULT_PAGE, PROXY_SETTING, PROXY_INDEXERS, \
            AUTOPOSTPROCESSER_FREQUENCY, SHOWUPDATE_HOUR, \
            ANIME_DEFAULT, NAMING_ANIME, ANIMESUPPORT, USE_ANIDB, ANIDB_USERNAME, ANIDB_PASSWORD, ANIDB_USE_MYLIST, \
            ANIME_SPLIT_HOME, SCENE_DEFAULT, ARCHIVE_DEFAULT, DOWNLOAD_URL, BACKLOG_DAYS, GIT_USERNAME, GIT_PASSWORD, \
            GIT_AUTOISSUES, DEVELOPER, gh, DISPLAY_ALL_SEASONS, SSL_VERIFY, NEWS_LAST_READ, NEWS_LATEST, SOCKET_TIMEOUT

        if __INITIALIZED__:
            return False

        CheckSection(CFG, 'General')
        CheckSection(CFG, 'Blackhole')
        CheckSection(CFG, 'Newzbin')
        CheckSection(CFG, 'SABnzbd')
        CheckSection(CFG, 'NZBget')
        CheckSection(CFG, 'KODI')
        CheckSection(CFG, 'PLEX')
        CheckSection(CFG, 'Emby')
        CheckSection(CFG, 'Growl')
        CheckSection(CFG, 'Prowl')
        CheckSection(CFG, 'Twitter')
        CheckSection(CFG, 'Boxcar')
        CheckSection(CFG, 'Boxcar2')
        CheckSection(CFG, 'NMJ')
        CheckSection(CFG, 'NMJv2')
        CheckSection(CFG, 'Synology')
        CheckSection(CFG, 'SynologyNotifier')
        CheckSection(CFG, 'pyTivo')
        CheckSection(CFG, 'NMA')
        CheckSection(CFG, 'Pushalot')
        CheckSection(CFG, 'Pushbullet')
        CheckSection(CFG, 'Subtitles')
        CheckSection(CFG, 'pyTivo')

        # Need to be before any passwords
        ENCRYPTION_VERSION = check_setting_int(CFG, 'General', 'encryption_version', 0)
        ENCRYPTION_SECRET = check_setting_str(CFG, 'General', 'encryption_secret', helpers.generateCookieSecret(), censor_log=True)

        GIT_AUTOISSUES = bool(check_setting_int(CFG, 'General', 'git_autoissues', 0))

        # git login info
        GIT_USERNAME = check_setting_str(CFG, 'General', 'git_username', '')
        GIT_PASSWORD = check_setting_str(CFG, 'General', 'git_password', '', censor_log=True)
        GIT_NEWVER = bool(check_setting_int(CFG, 'General', 'git_newver', 0))
        DEVELOPER = bool(check_setting_int(CFG, 'General', 'developer', 0))

        # debugging
        DEBUG = bool(check_setting_int(CFG, 'General', 'debug', 0))

        DEFAULT_PAGE = check_setting_str(CFG, 'General', 'default_page', 'home')
        if DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            DEFAULT_PAGE = 'home'

        ACTUAL_LOG_DIR = check_setting_str(CFG, 'General', 'log_dir', 'Logs')
        LOG_DIR = os.path.normpath(os.path.join(DATA_DIR, ACTUAL_LOG_DIR))
        LOG_NR = check_setting_int(CFG, 'General', 'log_nr', 5)  # Default to 5 backup file (sickrage.log.x)
        LOG_SIZE = check_setting_int(CFG, 'General', 'log_size', 1048576)  # Default to max 1MB per logfile
        fileLogging = True
        if not helpers.makeDir(LOG_DIR):
            sys.stderr.write("!!! No log folder, logging to screen only!\n")
            fileLogging = False

        # init logging
        logger.initLogging(consoleLogging=consoleLogging, fileLogging=fileLogging, debugLogging=DEBUG)

        # github api
        try:
            if not (GIT_USERNAME and GIT_PASSWORD):
                gh = Github(user_agent="SiCKRAGE").get_organization(GIT_ORG).get_repo(GIT_REPO)
            else:
                gh = Github(login_or_token=GIT_USERNAME, password=GIT_PASSWORD, user_agent="SiCKRAGE").get_organization(GIT_ORG).get_repo(GIT_REPO)
        except Exception as e:
            gh = None
            logger.log(u'Unable to setup GitHub properly. GitHub will not be available. Error: %s' % ex(e), logger.WARNING)

        # git reset on update
        GIT_RESET = bool(check_setting_int(CFG, 'General', 'git_reset', 1))

        # current git branch
        BRANCH = check_setting_str(CFG, 'General', 'branch', '')

        # git_remote
        GIT_REMOTE = check_setting_str(CFG, 'General', 'git_remote', 'origin')
        GIT_REMOTE_URL = check_setting_str(CFG, 'General', 'git_remote_url',
                                           'https://github.com/%s/%s.git' % (GIT_ORG, GIT_REPO))

        # current commit hash
        CUR_COMMIT_HASH = check_setting_str(CFG, 'General', 'cur_commit_hash', '')

        # current commit branch
        CUR_COMMIT_BRANCH = check_setting_str(CFG, 'General', 'cur_commit_branch', '')

        ACTUAL_CACHE_DIR = check_setting_str(CFG, 'General', 'cache_dir', 'cache')

        # fix bad configs due to buggy code
        if ACTUAL_CACHE_DIR == 'None':
            ACTUAL_CACHE_DIR = 'cache'

        # unless they specify, put the cache dir inside the data dir
        if not os.path.isabs(ACTUAL_CACHE_DIR):
            CACHE_DIR = os.path.join(DATA_DIR, ACTUAL_CACHE_DIR)
        else:
            CACHE_DIR = ACTUAL_CACHE_DIR

        if not helpers.makeDir(CACHE_DIR):
            logger.log(u"!!! Creating local cache dir failed, using system default", logger.ERROR)
            CACHE_DIR = None

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
                            bakFilename = '{0}-{1}'.format(path_leaf(dstDir), datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S'))
                            shutil.move(dstDir, os.path.join(os.path.dirname(dstDir), bakFilename))

                        shutil.move(srcDir, dstDir)
                        logger.log(u"Restore: restoring cache successful", logger.INFO)
                    except Exception as e:
                        logger.log(u"Restore: restoring cache failed: {0}".format(str(e)), logger.ERROR)

                restoreCache(os.path.join(restoreDir, 'cache'), CACHE_DIR)
        except Exception as e:
            logger.log(u"Restore: restoring cache failed: {0}".format(ex(e)), logger.ERROR)
        finally:
            if os.path.exists(os.path.join(DATA_DIR, 'restore')):
                try:
                    shutil.rmtree(os.path.join(DATA_DIR, 'restore'))
                except Exception as e:
                    logger.log(u"Restore: Unable to remove the restore directory: {0}".format(ex(e)), logger.ERROR)

                for cleanupDir in ['mako', 'sessions', 'indexers']:
                    try:
                        shutil.rmtree(os.path.join(CACHE_DIR, cleanupDir))
                    except Exception as e:
                        logger.log(u"Restore: Unable to remove the cache/{0} directory: {1}".format(cleanupDir, ex(e)), logger.WARNING)


        GUI_NAME = check_setting_str(CFG, 'GUI', 'gui_name', 'slick')

        THEME_NAME = check_setting_str(CFG, 'GUI', 'theme_name', 'dark')

        SOCKET_TIMEOUT = check_setting_int(CFG, 'General', 'socket_timeout', 30)
        socket.setdefaulttimeout(SOCKET_TIMEOUT)

        try:
            WEB_PORT = check_setting_int(CFG, 'General', 'web_port', 8081)
        except Exception:
            WEB_PORT = 8081

        if WEB_PORT < 21 or WEB_PORT > 65535:
            WEB_PORT = 8081

        WEB_HOST = check_setting_str(CFG, 'General', 'web_host', '0.0.0.0')
        WEB_IPV6 = bool(check_setting_int(CFG, 'General', 'web_ipv6', 0))
        WEB_ROOT = check_setting_str(CFG, 'General', 'web_root', '').rstrip("/")
        WEB_LOG = bool(check_setting_int(CFG, 'General', 'web_log', 0))
        WEB_USERNAME = check_setting_str(CFG, 'General', 'web_username', '', censor_log=True)
        WEB_PASSWORD = check_setting_str(CFG, 'General', 'web_password', '', censor_log=True)
        WEB_COOKIE_SECRET = check_setting_str(CFG, 'General', 'web_cookie_secret', helpers.generateCookieSecret(), censor_log=True)
        if not WEB_COOKIE_SECRET:
            WEB_COOKIE_SECRET = helpers.generateCookieSecret()

        WEB_USE_GZIP = bool(check_setting_int(CFG, 'General', 'web_use_gzip', 1))

        SSL_VERIFY = bool(check_setting_int(CFG, 'General', 'ssl_verify', 1))

        INDEXER_DEFAULT_LANGUAGE = check_setting_str(CFG, 'General', 'indexerDefaultLang', 'en')
        EP_DEFAULT_DELETED_STATUS = check_setting_int(CFG, 'General', 'ep_default_deleted_status', 6)

        LAUNCH_BROWSER = bool(check_setting_int(CFG, 'General', 'launch_browser', 1))

        DOWNLOAD_URL = check_setting_str(CFG, 'General', 'download_url', "")

        LOCALHOST_IP = check_setting_str(CFG, 'General', 'localhost_ip', '')

        CPU_PRESET = check_setting_str(CFG, 'General', 'cpu_preset', 'NORMAL')

        ANON_REDIRECT = check_setting_str(CFG, 'General', 'anon_redirect', 'http://dereferer.org/?')
        PROXY_SETTING = check_setting_str(CFG, 'General', 'proxy_setting', '')
        PROXY_INDEXERS = bool(check_setting_int(CFG, 'General', 'proxy_indexers', 1))

        # attempt to help prevent users from breaking links by using a bad url
        if not ANON_REDIRECT.endswith('?'):
            ANON_REDIRECT = ''

        TRASH_REMOVE_SHOW = bool(check_setting_int(CFG, 'General', 'trash_remove_show', 0))
        TRASH_ROTATE_LOGS = bool(check_setting_int(CFG, 'General', 'trash_rotate_logs', 0))

        SORT_ARTICLE = bool(check_setting_int(CFG, 'General', 'sort_article', 0))

        API_KEY = check_setting_str(CFG, 'General', 'api_key', '', censor_log=True)

        ENABLE_HTTPS = bool(check_setting_int(CFG, 'General', 'enable_https', 0))

        HTTPS_CERT = check_setting_str(CFG, 'General', 'https_cert', 'server.crt')
        HTTPS_KEY = check_setting_str(CFG, 'General', 'https_key', 'server.key')

        HANDLE_REVERSE_PROXY = bool(check_setting_int(CFG, 'General', 'handle_reverse_proxy', 0))

        ROOT_DIRS = check_setting_str(CFG, 'General', 'root_dirs', '')
        if not re.match(r'\d+\|[^|]+(?:\|[^|]+)*', ROOT_DIRS):
            ROOT_DIRS = ''

        QUALITY_DEFAULT = check_setting_int(CFG, 'General', 'quality_default', SD)
        STATUS_DEFAULT = check_setting_int(CFG, 'General', 'status_default', SKIPPED)
        STATUS_DEFAULT_AFTER = check_setting_int(CFG, 'General', 'status_default_after', WANTED)
        VERSION_NOTIFY = bool(check_setting_int(CFG, 'General', 'version_notify', 1))
        AUTO_UPDATE = bool(check_setting_int(CFG, 'General', 'auto_update', 0))
        NOTIFY_ON_UPDATE = bool(check_setting_int(CFG, 'General', 'notify_on_update', 1))
        FLATTEN_FOLDERS_DEFAULT = bool(check_setting_int(CFG, 'General', 'flatten_folders_default', 0))
        INDEXER_DEFAULT = check_setting_int(CFG, 'General', 'indexer_default', 0)
        INDEXER_TIMEOUT = check_setting_int(CFG, 'General', 'indexer_timeout', 20)
        ANIME_DEFAULT = bool(check_setting_int(CFG, 'General', 'anime_default', 0))
        SCENE_DEFAULT = bool(check_setting_int(CFG, 'General', 'scene_default', 0))
        ARCHIVE_DEFAULT = bool(check_setting_int(CFG, 'General', 'archive_default', 0))

        PROVIDER_ORDER = check_setting_str(CFG, 'General', 'provider_order', '').split()

        NAMING_PATTERN = check_setting_str(CFG, 'General', 'naming_pattern', 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ABD_PATTERN = check_setting_str(CFG, 'General', 'naming_abd_pattern', '%SN - %A.D - %EN')
        NAMING_CUSTOM_ABD = bool(check_setting_int(CFG, 'General', 'naming_custom_abd', 0))
        NAMING_SPORTS_PATTERN = check_setting_str(CFG, 'General', 'naming_sports_pattern', '%SN - %A-D - %EN')
        NAMING_ANIME_PATTERN = check_setting_str(CFG, 'General', 'naming_anime_pattern',
                                                 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ANIME = check_setting_int(CFG, 'General', 'naming_anime', 3)
        NAMING_CUSTOM_SPORTS = bool(check_setting_int(CFG, 'General', 'naming_custom_sports', 0))
        NAMING_CUSTOM_ANIME = bool(check_setting_int(CFG, 'General', 'naming_custom_anime', 0))
        NAMING_MULTI_EP = check_setting_int(CFG, 'General', 'naming_multi_ep', 1)
        NAMING_ANIME_MULTI_EP = check_setting_int(CFG, 'General', 'naming_anime_multi_ep', 1)
        NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        NAMING_STRIP_YEAR = bool(check_setting_int(CFG, 'General', 'naming_strip_year', 0))

        USE_NZBS = bool(check_setting_int(CFG, 'General', 'use_nzbs', 0))
        USE_TORRENTS = bool(check_setting_int(CFG, 'General', 'use_torrents', 1))

        NZB_METHOD = check_setting_str(CFG, 'General', 'nzb_method', 'blackhole')
        if NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget'):
            NZB_METHOD = 'blackhole'

        TORRENT_METHOD = check_setting_str(CFG, 'General', 'torrent_method', 'blackhole')
        if TORRENT_METHOD not in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet'):
            TORRENT_METHOD = 'blackhole'

        DOWNLOAD_PROPERS = bool(check_setting_int(CFG, 'General', 'download_propers', 1))
        CHECK_PROPERS_INTERVAL = check_setting_str(CFG, 'General', 'check_propers_interval', '')
        if CHECK_PROPERS_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            CHECK_PROPERS_INTERVAL = 'daily'

        RANDOMIZE_PROVIDERS = bool(check_setting_int(CFG, 'General', 'randomize_providers', 0))

        ALLOW_HIGH_PRIORITY = bool(check_setting_int(CFG, 'General', 'allow_high_priority', 1))

        SKIP_REMOVED_FILES = bool(check_setting_int(CFG, 'General', 'skip_removed_files', 0))

        USENET_RETENTION = check_setting_int(CFG, 'General', 'usenet_retention', 500)

        AUTOPOSTPROCESSER_FREQUENCY = check_setting_int(CFG, 'General', 'autopostprocesser_frequency',
                                                        DEFAULT_AUTOPOSTPROCESSER_FREQUENCY)
        if AUTOPOSTPROCESSER_FREQUENCY < MIN_AUTOPOSTPROCESSER_FREQUENCY:
            AUTOPOSTPROCESSER_FREQUENCY = MIN_AUTOPOSTPROCESSER_FREQUENCY

        DAILYSEARCH_FREQUENCY = check_setting_int(CFG, 'General', 'dailysearch_frequency',
                                                  DEFAULT_DAILYSEARCH_FREQUENCY)
        if DAILYSEARCH_FREQUENCY < MIN_DAILYSEARCH_FREQUENCY:
            DAILYSEARCH_FREQUENCY = MIN_DAILYSEARCH_FREQUENCY

        MIN_BACKLOG_FREQUENCY = get_backlog_cycle_time()
        BACKLOG_FREQUENCY = check_setting_int(CFG, 'General', 'backlog_frequency', DEFAULT_BACKLOG_FREQUENCY)
        if BACKLOG_FREQUENCY < MIN_BACKLOG_FREQUENCY:
            BACKLOG_FREQUENCY = MIN_BACKLOG_FREQUENCY

        UPDATE_FREQUENCY = check_setting_int(CFG, 'General', 'update_frequency', DEFAULT_UPDATE_FREQUENCY)
        if UPDATE_FREQUENCY < MIN_UPDATE_FREQUENCY:
            UPDATE_FREQUENCY = MIN_UPDATE_FREQUENCY

        SHOWUPDATE_HOUR = check_setting_int(CFG, 'General', 'showupdate_hour', DEFAULT_SHOWUPDATE_HOUR)
        if SHOWUPDATE_HOUR > 23:
            SHOWUPDATE_HOUR = 0
        elif SHOWUPDATE_HOUR < 0:
            SHOWUPDATE_HOUR = 0

        BACKLOG_DAYS = check_setting_int(CFG, 'General', 'backlog_days', 7)

        NEWS_LAST_READ = check_setting_str(CFG, 'General', 'news_last_read', '1970-01-01')
        NEWS_LATEST = NEWS_LAST_READ

        NZB_DIR = check_setting_str(CFG, 'Blackhole', 'nzb_dir', '')
        TORRENT_DIR = check_setting_str(CFG, 'Blackhole', 'torrent_dir', '')

        TV_DOWNLOAD_DIR = check_setting_str(CFG, 'General', 'tv_download_dir', '')
        PROCESS_AUTOMATICALLY = bool(check_setting_int(CFG, 'General', 'process_automatically', 0))
        NO_DELETE = bool(check_setting_int(CFG, 'General', 'no_delete', 0))
        UNPACK = bool(check_setting_int(CFG, 'General', 'unpack', 0))
        RENAME_EPISODES = bool(check_setting_int(CFG, 'General', 'rename_episodes', 1))
        AIRDATE_EPISODES = bool(check_setting_int(CFG, 'General', 'airdate_episodes', 0))
        FILE_TIMESTAMP_TIMEZONE = check_setting_str(CFG, 'General', 'file_timestamp_timezone', 'network')
        KEEP_PROCESSED_DIR = bool(check_setting_int(CFG, 'General', 'keep_processed_dir', 1))
        PROCESS_METHOD = check_setting_str(CFG, 'General', 'process_method', 'copy' if KEEP_PROCESSED_DIR else 'move')
        DELRARCONTENTS = bool(check_setting_int(CFG, 'General', 'del_rar_contents', 0))
        MOVE_ASSOCIATED_FILES = bool(check_setting_int(CFG, 'General', 'move_associated_files', 0))
        POSTPONE_IF_SYNC_FILES = bool(check_setting_int(CFG, 'General', 'postpone_if_sync_files', 1))
        SYNC_FILES = check_setting_str(CFG, 'General', 'sync_files', SYNC_FILES)
        NFO_RENAME = bool(check_setting_int(CFG, 'General', 'nfo_rename', 1))
        CREATE_MISSING_SHOW_DIRS = bool(check_setting_int(CFG, 'General', 'create_missing_show_dirs', 0))
        ADD_SHOWS_WO_DIR = bool(check_setting_int(CFG, 'General', 'add_shows_wo_dir', 0))

        NZBS = bool(check_setting_int(CFG, 'NZBs', 'nzbs', 0))
        NZBS_UID = check_setting_str(CFG, 'NZBs', 'nzbs_uid', '', censor_log=True)
        NZBS_HASH = check_setting_str(CFG, 'NZBs', 'nzbs_hash', '', censor_log=True)

        NEWZBIN = bool(check_setting_int(CFG, 'Newzbin', 'newzbin', 0))
        NEWZBIN_USERNAME = check_setting_str(CFG, 'Newzbin', 'newzbin_username', '', censor_log=True)
        NEWZBIN_PASSWORD = check_setting_str(CFG, 'Newzbin', 'newzbin_password', '', censor_log=True)

        SAB_USERNAME = check_setting_str(CFG, 'SABnzbd', 'sab_username', '', censor_log=True)
        SAB_PASSWORD = check_setting_str(CFG, 'SABnzbd', 'sab_password', '', censor_log=True)
        SAB_APIKEY = check_setting_str(CFG, 'SABnzbd', 'sab_apikey', '', censor_log=True)
        SAB_CATEGORY = check_setting_str(CFG, 'SABnzbd', 'sab_category', 'tv')
        SAB_CATEGORY_BACKLOG = check_setting_str(CFG, 'SABnzbd', 'sab_category_backlog', SAB_CATEGORY)
        SAB_CATEGORY_ANIME = check_setting_str(CFG, 'SABnzbd', 'sab_category_anime', 'anime')
        SAB_CATEGORY_ANIME_BACKLOG = check_setting_str(CFG, 'SABnzbd', 'sab_category_anime_backlog', SAB_CATEGORY_ANIME)
        SAB_HOST = check_setting_str(CFG, 'SABnzbd', 'sab_host', '')
        SAB_FORCED = bool(check_setting_int(CFG, 'SABnzbd', 'sab_forced', 0))

        NZBGET_USERNAME = check_setting_str(CFG, 'NZBget', 'nzbget_username', 'nzbget', censor_log=True)
        NZBGET_PASSWORD = check_setting_str(CFG, 'NZBget', 'nzbget_password', 'tegbzn6789', censor_log=True)
        NZBGET_CATEGORY = check_setting_str(CFG, 'NZBget', 'nzbget_category', 'tv')
        NZBGET_CATEGORY_BACKLOG = check_setting_str(CFG, 'NZBget', 'nzbget_category_backlog', NZBGET_CATEGORY)
        NZBGET_CATEGORY_ANIME = check_setting_str(CFG, 'NZBget', 'nzbget_category_anime', 'anime')
        NZBGET_CATEGORY_ANIME_BACKLOG = check_setting_str(CFG, 'NZBget', 'nzbget_category_anime_backlog', NZBGET_CATEGORY_ANIME)
        NZBGET_HOST = check_setting_str(CFG, 'NZBget', 'nzbget_host', '')
        NZBGET_USE_HTTPS = bool(check_setting_int(CFG, 'NZBget', 'nzbget_use_https', 0))
        NZBGET_PRIORITY = check_setting_int(CFG, 'NZBget', 'nzbget_priority', 100)

        TORRENT_USERNAME = check_setting_str(CFG, 'TORRENT', 'torrent_username', '', censor_log=True)
        TORRENT_PASSWORD = check_setting_str(CFG, 'TORRENT', 'torrent_password', '', censor_log=True)
        TORRENT_HOST = check_setting_str(CFG, 'TORRENT', 'torrent_host', '')
        TORRENT_PATH = check_setting_str(CFG, 'TORRENT', 'torrent_path', '')
        TORRENT_SEED_TIME = check_setting_int(CFG, 'TORRENT', 'torrent_seed_time', 0)
        TORRENT_PAUSED = bool(check_setting_int(CFG, 'TORRENT', 'torrent_paused', 0))
        TORRENT_HIGH_BANDWIDTH = bool(check_setting_int(CFG, 'TORRENT', 'torrent_high_bandwidth', 0))
        TORRENT_LABEL = check_setting_str(CFG, 'TORRENT', 'torrent_label', '')
        TORRENT_LABEL_ANIME = check_setting_str(CFG, 'TORRENT', 'torrent_label_anime', '')
        TORRENT_VERIFY_CERT = bool(check_setting_int(CFG, 'TORRENT', 'torrent_verify_cert', 0))
        TORRENT_RPCURL = check_setting_str(CFG, 'TORRENT', 'torrent_rpcurl', 'transmission')
        TORRENT_AUTH_TYPE = check_setting_str(CFG, 'TORRENT', 'torrent_auth_type', '')

        USE_KODI = bool(check_setting_int(CFG, 'KODI', 'use_kodi', 0))
        KODI_ALWAYS_ON = bool(check_setting_int(CFG, 'KODI', 'kodi_always_on', 1))
        KODI_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'KODI', 'kodi_notify_onsnatch', 0))
        KODI_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'KODI', 'kodi_notify_ondownload', 0))
        KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'KODI', 'kodi_notify_onsubtitledownload', 0))
        KODI_UPDATE_LIBRARY = bool(check_setting_int(CFG, 'KODI', 'kodi_update_library', 0))
        KODI_UPDATE_FULL = bool(check_setting_int(CFG, 'KODI', 'kodi_update_full', 0))
        KODI_UPDATE_ONLYFIRST = bool(check_setting_int(CFG, 'KODI', 'kodi_update_onlyfirst', 0))
        KODI_HOST = check_setting_str(CFG, 'KODI', 'kodi_host', '')
        KODI_USERNAME = check_setting_str(CFG, 'KODI', 'kodi_username', '', censor_log=True)
        KODI_PASSWORD = check_setting_str(CFG, 'KODI', 'kodi_password', '', censor_log=True)

        USE_PLEX = bool(check_setting_int(CFG, 'Plex', 'use_plex', 0))
        PLEX_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Plex', 'plex_notify_onsnatch', 0))
        PLEX_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Plex', 'plex_notify_ondownload', 0))
        PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Plex', 'plex_notify_onsubtitledownload', 0))
        PLEX_UPDATE_LIBRARY = bool(check_setting_int(CFG, 'Plex', 'plex_update_library', 0))
        PLEX_SERVER_HOST = check_setting_str(CFG, 'Plex', 'plex_server_host', '')
        PLEX_SERVER_TOKEN = check_setting_str(CFG, 'Plex', 'plex_server_token', '')
        PLEX_HOST = check_setting_str(CFG, 'Plex', 'plex_host', '')
        PLEX_USERNAME = check_setting_str(CFG, 'Plex', 'plex_username', '', censor_log=True)
        PLEX_PASSWORD = check_setting_str(CFG, 'Plex', 'plex_password', '', censor_log=True)
        USE_PLEX_CLIENT = bool(check_setting_int(CFG, 'Plex', 'use_plex_client', 0))
        PLEX_CLIENT_USERNAME = check_setting_str(CFG, 'Plex', 'plex_client_username', '', censor_log=True)
        PLEX_CLIENT_PASSWORD = check_setting_str(CFG, 'Plex', 'plex_client_password', '', censor_log=True)

        USE_EMBY = bool(check_setting_int(CFG, 'Emby', 'use_emby', 0))
        EMBY_HOST = check_setting_str(CFG, 'Emby', 'emby_host', '')
        EMBY_APIKEY = check_setting_str(CFG, 'Emby', 'emby_apikey', '')

        USE_GROWL = bool(check_setting_int(CFG, 'Growl', 'use_growl', 0))
        GROWL_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Growl', 'growl_notify_onsnatch', 0))
        GROWL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Growl', 'growl_notify_ondownload', 0))
        GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Growl', 'growl_notify_onsubtitledownload', 0))
        GROWL_HOST = check_setting_str(CFG, 'Growl', 'growl_host', '')
        GROWL_PASSWORD = check_setting_str(CFG, 'Growl', 'growl_password', '', censor_log=True)

        USE_FREEMOBILE = bool(check_setting_int(CFG, 'FreeMobile', 'use_freemobile', 0))
        FREEMOBILE_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'FreeMobile', 'freemobile_notify_onsnatch', 0))
        FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'FreeMobile', 'freemobile_notify_ondownload', 0))
        FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'FreeMobile', 'freemobile_notify_onsubtitledownload', 0))
        FREEMOBILE_ID = check_setting_str(CFG, 'FreeMobile', 'freemobile_id', '')
        FREEMOBILE_APIKEY = check_setting_str(CFG, 'FreeMobile', 'freemobile_apikey', '')

        USE_PROWL = bool(check_setting_int(CFG, 'Prowl', 'use_prowl', 0))
        PROWL_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Prowl', 'prowl_notify_onsnatch', 0))
        PROWL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Prowl', 'prowl_notify_ondownload', 0))
        PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Prowl', 'prowl_notify_onsubtitledownload', 0))
        PROWL_API = check_setting_str(CFG, 'Prowl', 'prowl_api', '', censor_log=True)
        PROWL_PRIORITY = check_setting_str(CFG, 'Prowl', 'prowl_priority', "0")

        USE_TWITTER = bool(check_setting_int(CFG, 'Twitter', 'use_twitter', 0))
        TWITTER_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Twitter', 'twitter_notify_onsnatch', 0))
        TWITTER_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Twitter', 'twitter_notify_ondownload', 0))
        TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(CFG, 'Twitter', 'twitter_notify_onsubtitledownload', 0))
        TWITTER_USERNAME = check_setting_str(CFG, 'Twitter', 'twitter_username', '', censor_log=True)
        TWITTER_PASSWORD = check_setting_str(CFG, 'Twitter', 'twitter_password', '', censor_log=True)
        TWITTER_PREFIX = check_setting_str(CFG, 'Twitter', 'twitter_prefix', GIT_REPO)
        TWITTER_DMTO = check_setting_str(CFG, 'Twitter', 'twitter_dmto', '')
        TWITTER_USEDM = bool(check_setting_int(CFG, 'Twitter', 'twitter_usedm', 0))

        USE_BOXCAR = bool(check_setting_int(CFG, 'Boxcar', 'use_boxcar', 0))
        BOXCAR_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Boxcar', 'boxcar_notify_onsnatch', 0))
        BOXCAR_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Boxcar', 'boxcar_notify_ondownload', 0))
        BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Boxcar', 'boxcar_notify_onsubtitledownload', 0))
        BOXCAR_USERNAME = check_setting_str(CFG, 'Boxcar', 'boxcar_username', '', censor_log=True)

        USE_BOXCAR2 = bool(check_setting_int(CFG, 'Boxcar2', 'use_boxcar2', 0))
        BOXCAR2_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Boxcar2', 'boxcar2_notify_onsnatch', 0))
        BOXCAR2_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Boxcar2', 'boxcar2_notify_ondownload', 0))
        BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Boxcar2', 'boxcar2_notify_onsubtitledownload', 0))
        BOXCAR2_ACCESSTOKEN = check_setting_str(CFG, 'Boxcar2', 'boxcar2_accesstoken', '', censor_log=True)

        USE_PUSHOVER = bool(check_setting_int(CFG, 'Pushover', 'use_pushover', 0))
        PUSHOVER_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Pushover', 'pushover_notify_onsnatch', 0))
        PUSHOVER_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Pushover', 'pushover_notify_ondownload', 0))
        PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Pushover', 'pushover_notify_onsubtitledownload', 0))
        PUSHOVER_USERKEY = check_setting_str(CFG, 'Pushover', 'pushover_userkey', '', censor_log=True)
        PUSHOVER_APIKEY = check_setting_str(CFG, 'Pushover', 'pushover_apikey', '', censor_log=True)
        PUSHOVER_DEVICE = check_setting_str(CFG, 'Pushover', 'pushover_device', '')
        PUSHOVER_SOUND = check_setting_str(CFG, 'Pushover', 'pushover_sound', 'pushover')

        USE_LIBNOTIFY = bool(check_setting_int(CFG, 'Libnotify', 'use_libnotify', 0))
        LIBNOTIFY_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Libnotify', 'libnotify_notify_onsnatch', 0))
        LIBNOTIFY_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Libnotify', 'libnotify_notify_ondownload', 0))
        LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Libnotify', 'libnotify_notify_onsubtitledownload', 0))

        USE_NMJ = bool(check_setting_int(CFG, 'NMJ', 'use_nmj', 0))
        NMJ_HOST = check_setting_str(CFG, 'NMJ', 'nmj_host', '')
        NMJ_DATABASE = check_setting_str(CFG, 'NMJ', 'nmj_database', '')
        NMJ_MOUNT = check_setting_str(CFG, 'NMJ', 'nmj_mount', '')

        USE_NMJv2 = bool(check_setting_int(CFG, 'NMJv2', 'use_nmjv2', 0))
        NMJv2_HOST = check_setting_str(CFG, 'NMJv2', 'nmjv2_host', '')
        NMJv2_DATABASE = check_setting_str(CFG, 'NMJv2', 'nmjv2_database', '')
        NMJv2_DBLOC = check_setting_str(CFG, 'NMJv2', 'nmjv2_dbloc', '')

        USE_SYNOINDEX = bool(check_setting_int(CFG, 'Synology', 'use_synoindex', 0))

        USE_SYNOLOGYNOTIFIER = bool(check_setting_int(CFG, 'SynologyNotifier', 'use_synologynotifier', 0))
        SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = bool(
            check_setting_int(CFG, 'SynologyNotifier', 'synologynotifier_notify_onsnatch', 0))
        SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = bool(
            check_setting_int(CFG, 'SynologyNotifier', 'synologynotifier_notify_ondownload', 0))
        SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(CFG, 'SynologyNotifier', 'synologynotifier_notify_onsubtitledownload', 0))

        USE_TRAKT = bool(check_setting_int(CFG, 'Trakt', 'use_trakt', 0))
        TRAKT_USERNAME = check_setting_str(CFG, 'Trakt', 'trakt_username', '', censor_log=True)
        TRAKT_ACCESS_TOKEN = check_setting_str(CFG, 'Trakt', 'trakt_access_token', '', censor_log=True)
        TRAKT_REFRESH_TOKEN = check_setting_str(CFG, 'Trakt', 'trakt_refresh_token', '', censor_log=True)
        TRAKT_REMOVE_WATCHLIST = bool(check_setting_int(CFG, 'Trakt', 'trakt_remove_watchlist', 0))
        TRAKT_REMOVE_SERIESLIST = bool(check_setting_int(CFG, 'Trakt', 'trakt_remove_serieslist', 0))
        TRAKT_REMOVE_SHOW_FROM_SICKRAGE = bool(check_setting_int(CFG, 'Trakt', 'trakt_remove_show_from_sickrage', 0))
        TRAKT_SYNC_WATCHLIST = bool(check_setting_int(CFG, 'Trakt', 'trakt_sync_watchlist', 0))
        TRAKT_METHOD_ADD = check_setting_int(CFG, 'Trakt', 'trakt_method_add', 0)
        TRAKT_START_PAUSED = bool(check_setting_int(CFG, 'Trakt', 'trakt_start_paused', 0))
        TRAKT_USE_RECOMMENDED = bool(check_setting_int(CFG, 'Trakt', 'trakt_use_recommended', 0))
        TRAKT_SYNC = bool(check_setting_int(CFG, 'Trakt', 'trakt_sync', 0))
        TRAKT_SYNC_REMOVE = bool(check_setting_int(CFG, 'Trakt', 'trakt_sync_remove', 0))
        TRAKT_DEFAULT_INDEXER = check_setting_int(CFG, 'Trakt', 'trakt_default_indexer', 1)
        TRAKT_TIMEOUT = check_setting_int(CFG, 'Trakt', 'trakt_timeout', 30)
        TRAKT_BLACKLIST_NAME = check_setting_str(CFG, 'Trakt', 'trakt_blacklist_name', '')

        USE_PYTIVO = bool(check_setting_int(CFG, 'pyTivo', 'use_pytivo', 0))
        PYTIVO_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'pyTivo', 'pytivo_notify_onsnatch', 0))
        PYTIVO_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'pyTivo', 'pytivo_notify_ondownload', 0))
        PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'pyTivo', 'pytivo_notify_onsubtitledownload', 0))
        PYTIVO_UPDATE_LIBRARY = bool(check_setting_int(CFG, 'pyTivo', 'pyTivo_update_library', 0))
        PYTIVO_HOST = check_setting_str(CFG, 'pyTivo', 'pytivo_host', '')
        PYTIVO_SHARE_NAME = check_setting_str(CFG, 'pyTivo', 'pytivo_share_name', '')
        PYTIVO_TIVO_NAME = check_setting_str(CFG, 'pyTivo', 'pytivo_tivo_name', '')

        USE_NMA = bool(check_setting_int(CFG, 'NMA', 'use_nma', 0))
        NMA_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'NMA', 'nma_notify_onsnatch', 0))
        NMA_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'NMA', 'nma_notify_ondownload', 0))
        NMA_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'NMA', 'nma_notify_onsubtitledownload', 0))
        NMA_API = check_setting_str(CFG, 'NMA', 'nma_api', '', censor_log=True)
        NMA_PRIORITY = check_setting_str(CFG, 'NMA', 'nma_priority', "0")

        USE_PUSHALOT = bool(check_setting_int(CFG, 'Pushalot', 'use_pushalot', 0))
        PUSHALOT_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Pushalot', 'pushalot_notify_onsnatch', 0))
        PUSHALOT_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Pushalot', 'pushalot_notify_ondownload', 0))
        PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(CFG, 'Pushalot', 'pushalot_notify_onsubtitledownload', 0))
        PUSHALOT_AUTHORIZATIONTOKEN = check_setting_str(CFG, 'Pushalot', 'pushalot_authorizationtoken', '', censor_log=True)

        USE_PUSHBULLET = bool(check_setting_int(CFG, 'Pushbullet', 'use_pushbullet', 0))
        PUSHBULLET_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Pushbullet', 'pushbullet_notify_onsnatch', 0))
        PUSHBULLET_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Pushbullet', 'pushbullet_notify_ondownload', 0))
        PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = bool(
            check_setting_int(CFG, 'Pushbullet', 'pushbullet_notify_onsubtitledownload', 0))
        PUSHBULLET_API = check_setting_str(CFG, 'Pushbullet', 'pushbullet_api', '', censor_log=True)
        PUSHBULLET_DEVICE = check_setting_str(CFG, 'Pushbullet', 'pushbullet_device', '')

        USE_EMAIL = bool(check_setting_int(CFG, 'Email', 'use_email', 0))
        EMAIL_NOTIFY_ONSNATCH = bool(check_setting_int(CFG, 'Email', 'email_notify_onsnatch', 0))
        EMAIL_NOTIFY_ONDOWNLOAD = bool(check_setting_int(CFG, 'Email', 'email_notify_ondownload', 0))
        EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(check_setting_int(CFG, 'Email', 'email_notify_onsubtitledownload', 0))
        EMAIL_HOST = check_setting_str(CFG, 'Email', 'email_host', '')
        EMAIL_PORT = check_setting_int(CFG, 'Email', 'email_port', 25)
        EMAIL_TLS = bool(check_setting_int(CFG, 'Email', 'email_tls', 0))
        EMAIL_USER = check_setting_str(CFG, 'Email', 'email_user', '', censor_log=True)
        EMAIL_PASSWORD = check_setting_str(CFG, 'Email', 'email_password', '', censor_log=True)
        EMAIL_FROM = check_setting_str(CFG, 'Email', 'email_from', '')
        EMAIL_LIST = check_setting_str(CFG, 'Email', 'email_list', '')

        USE_SUBTITLES = bool(check_setting_int(CFG, 'Subtitles', 'use_subtitles', 0))
        SUBTITLES_LANGUAGES = check_setting_str(CFG, 'Subtitles', 'subtitles_languages', '').split(',')
        if SUBTITLES_LANGUAGES[0] == '':
            SUBTITLES_LANGUAGES = []
        SUBTITLES_DIR = check_setting_str(CFG, 'Subtitles', 'subtitles_dir', '')
        SUBTITLES_SERVICES_LIST = check_setting_str(CFG, 'Subtitles', 'SUBTITLES_SERVICES_LIST', '').split(',')
        SUBTITLES_SERVICES_ENABLED = [int(x) for x in
                                      check_setting_str(CFG, 'Subtitles', 'SUBTITLES_SERVICES_ENABLED', '').split('|')
                                      if x]
        SUBTITLES_DEFAULT = bool(check_setting_int(CFG, 'Subtitles', 'subtitles_default', 0))
        SUBTITLES_HISTORY = bool(check_setting_int(CFG, 'Subtitles', 'subtitles_history', 0))
        EMBEDDED_SUBTITLES_ALL = bool(check_setting_int(CFG, 'Subtitles', 'embedded_subtitles_all', 0))
        SUBTITLES_HEARING_IMPAIRED = bool(check_setting_int(CFG, 'Subtitles', 'subtitles_hearing_impaired', 0))
        SUBTITLES_FINDER_FREQUENCY = check_setting_int(CFG, 'Subtitles', 'subtitles_finder_frequency', 1)
        SUBTITLES_MULTI = bool(check_setting_int(CFG, 'Subtitles', 'subtitles_multi', 1))

        SUBTITLES_EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(CFG, 'Subtitles', 'subtitles_extra_scripts', '').split('|') if x.strip()]

        ADDIC7ED_USER = check_setting_str(CFG, 'Subtitles', 'addic7ed_username', '', censor_log=True)
        ADDIC7ED_PASS = check_setting_str(CFG, 'Subtitles', 'addic7ed_password', '', censor_log=True)

        LEGENDASTV_USER = check_setting_str(CFG, 'Subtitles', 'legendastv_username', '', censor_log=True)
        LEGENDASTV_PASS = check_setting_str(CFG, 'Subtitles', 'legendastv_password', '', censor_log=True)

        OPENSUBTITLES_USER = check_setting_str(CFG, 'Subtitles', 'opensubtitles_username', '', censor_log=True)
        OPENSUBTITLES_PASS = check_setting_str(CFG, 'Subtitles', 'opensubtitles_password', '', censor_log=True)

        USE_FAILED_DOWNLOADS = bool(check_setting_int(CFG, 'FailedDownloads', 'use_failed_downloads', 0))
        DELETE_FAILED = bool(check_setting_int(CFG, 'FailedDownloads', 'delete_failed', 0))

        GIT_PATH = check_setting_str(CFG, 'General', 'git_path', '')

        IGNORE_WORDS = check_setting_str(CFG, 'General', 'ignore_words', IGNORE_WORDS)
        REQUIRE_WORDS = check_setting_str(CFG, 'General', 'require_words', REQUIRE_WORDS)
        IGNORED_SUBS_LIST = check_setting_str(CFG, 'General', 'ignored_subs_list', IGNORED_SUBS_LIST)

        CALENDAR_UNPROTECTED = bool(check_setting_int(CFG, 'General', 'calendar_unprotected', 0))
        CALENDAR_ICONS = bool(check_setting_int(CFG, 'General', 'calendar_icons', 0))

        NO_RESTART = bool(check_setting_int(CFG, 'General', 'no_restart', 0))

        EXTRA_SCRIPTS = [x.strip() for x in check_setting_str(CFG, 'General', 'extra_scripts', '').split('|') if
                         x.strip()]

        USE_LISTVIEW = bool(check_setting_int(CFG, 'General', 'use_listview', 0))

        ANIMESUPPORT = False
        USE_ANIDB = bool(check_setting_int(CFG, 'ANIDB', 'use_anidb', 0))
        ANIDB_USERNAME = check_setting_str(CFG, 'ANIDB', 'anidb_username', '', censor_log=True)
        ANIDB_PASSWORD = check_setting_str(CFG, 'ANIDB', 'anidb_password', '', censor_log=True)
        ANIDB_USE_MYLIST = bool(check_setting_int(CFG, 'ANIDB', 'anidb_use_mylist', 0))

        ANIME_SPLIT_HOME = bool(check_setting_int(CFG, 'ANIME', 'anime_split_home', 0))

        METADATA_KODI = check_setting_str(CFG, 'General', 'metadata_kodi', '0|0|0|0|0|0|0|0|0|0')
        METADATA_KODI_12PLUS = check_setting_str(CFG, 'General', 'metadata_kodi_12plus', '0|0|0|0|0|0|0|0|0|0')
        METADATA_MEDIABROWSER = check_setting_str(CFG, 'General', 'metadata_mediabrowser', '0|0|0|0|0|0|0|0|0|0')
        METADATA_PS3 = check_setting_str(CFG, 'General', 'metadata_ps3', '0|0|0|0|0|0|0|0|0|0')
        METADATA_WDTV = check_setting_str(CFG, 'General', 'metadata_wdtv', '0|0|0|0|0|0|0|0|0|0')
        METADATA_TIVO = check_setting_str(CFG, 'General', 'metadata_tivo', '0|0|0|0|0|0|0|0|0|0')
        METADATA_MEDE8ER = check_setting_str(CFG, 'General', 'metadata_mede8er', '0|0|0|0|0|0|0|0|0|0')

        HOME_LAYOUT = check_setting_str(CFG, 'GUI', 'home_layout', 'poster')
        HISTORY_LAYOUT = check_setting_str(CFG, 'GUI', 'history_layout', 'detailed')
        HISTORY_LIMIT = check_setting_str(CFG, 'GUI', 'history_limit', '100')
        DISPLAY_SHOW_SPECIALS = bool(check_setting_int(CFG, 'GUI', 'display_show_specials', 1))
        COMING_EPS_LAYOUT = check_setting_str(CFG, 'GUI', 'coming_eps_layout', 'banner')
        COMING_EPS_DISPLAY_PAUSED = bool(check_setting_int(CFG, 'GUI', 'coming_eps_display_paused', 0))
        COMING_EPS_SORT = check_setting_str(CFG, 'GUI', 'coming_eps_sort', 'date')
        COMING_EPS_MISSED_RANGE = check_setting_int(CFG, 'GUI', 'coming_eps_missed_range', 7)
        FUZZY_DATING = bool(check_setting_int(CFG, 'GUI', 'fuzzy_dating', 0))
        TRIM_ZERO = bool(check_setting_int(CFG, 'GUI', 'trim_zero', 0))
        DATE_PRESET = check_setting_str(CFG, 'GUI', 'date_preset', '%x')
        TIME_PRESET_W_SECONDS = check_setting_str(CFG, 'GUI', 'time_preset', '%I:%M:%S %p')
        TIME_PRESET = TIME_PRESET_W_SECONDS.replace(u":%S", u"")
        TIMEZONE_DISPLAY = check_setting_str(CFG, 'GUI', 'timezone_display', 'local')
        POSTER_SORTBY = check_setting_str(CFG, 'GUI', 'poster_sortby', 'name')
        POSTER_SORTDIR = check_setting_int(CFG, 'GUI', 'poster_sortdir', 1)
        FILTER_ROW = bool(check_setting_int(CFG, 'GUI', 'filter_row', 1))
        DISPLAY_ALL_SEASONS = bool(check_setting_int(CFG, 'General', 'display_all_seasons', 1))

        # initialize NZB and TORRENT providers
        providerList = providers.makeProviderList()

        NEWZNAB_DATA = check_setting_str(CFG, 'Newznab', 'newznab_data', '')
        newznabProviderList = providers.getNewznabProviderList(NEWZNAB_DATA)

        TORRENTRSS_DATA = check_setting_str(CFG, 'TorrentRss', 'torrentrss_data', '')
        torrentRssProviderList = providers.getTorrentRssProviderList(TORRENTRSS_DATA)

        # dynamically load provider settings
        for curTorrentProvider in [curProvider for curProvider in providers.sortedProviderList() if
                                   curProvider.providerType == GenericProvider.TORRENT]:
            curTorrentProvider.enabled = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                curTorrentProvider.getID(), 0))
            if hasattr(curTorrentProvider, 'api_key'):
                curTorrentProvider.api_key = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                               curTorrentProvider.getID() + '_api_key', '', censor_log=True)
            if hasattr(curTorrentProvider, 'hash'):
                curTorrentProvider.hash = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                            curTorrentProvider.getID() + '_hash', '', censor_log=True)
            if hasattr(curTorrentProvider, 'digest'):
                curTorrentProvider.digest = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                              curTorrentProvider.getID() + '_digest', '', censor_log=True)
            if hasattr(curTorrentProvider, 'username'):
                curTorrentProvider.username = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                                curTorrentProvider.getID() + '_username', '', censor_log=True)
            if hasattr(curTorrentProvider, 'password'):
                curTorrentProvider.password = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                                curTorrentProvider.getID() + '_password', '', censor_log=True)
            if hasattr(curTorrentProvider, 'passkey'):
                curTorrentProvider.passkey = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                               curTorrentProvider.getID() + '_passkey', '', censor_log=True)
            if hasattr(curTorrentProvider, 'pin'):
                curTorrentProvider.pin = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                           curTorrentProvider.getID() + '_pin', '', censor_log=True)
            if hasattr(curTorrentProvider, 'confirmed'):
                curTorrentProvider.confirmed = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                      curTorrentProvider.getID() + '_confirmed', 1))
            if hasattr(curTorrentProvider, 'ranked'):
                curTorrentProvider.ranked = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                   curTorrentProvider.getID() + '_ranked', 1))

            if hasattr(curTorrentProvider, 'engrelease'):
                curTorrentProvider.engrelease = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                       curTorrentProvider.getID() + '_engrelease', 0))

            if hasattr(curTorrentProvider, 'onlyspasearch'):
                curTorrentProvider.onlyspasearch = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                          curTorrentProvider.getID() + '_onlyspasearch', 0))

            if hasattr(curTorrentProvider, 'sorting'):
                curTorrentProvider.sorting = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                               curTorrentProvider.getID() + '_sorting', 'seeders')
            if hasattr(curTorrentProvider, 'options'):
                curTorrentProvider.options = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                               curTorrentProvider.getID() + '_options', '')
            if hasattr(curTorrentProvider, 'ratio'):
                curTorrentProvider.ratio = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                             curTorrentProvider.getID() + '_ratio', '')
            if hasattr(curTorrentProvider, 'minseed'):
                curTorrentProvider.minseed = check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                               curTorrentProvider.getID() + '_minseed', 1)
            if hasattr(curTorrentProvider, 'minleech'):
                curTorrentProvider.minleech = check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                curTorrentProvider.getID() + '_minleech', 0)
            if hasattr(curTorrentProvider, 'freeleech'):
                curTorrentProvider.freeleech = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                      curTorrentProvider.getID() + '_freeleech', 0))
            if hasattr(curTorrentProvider, 'search_mode'):
                curTorrentProvider.search_mode = check_setting_str(CFG, curTorrentProvider.getID().upper(),
                                                                   curTorrentProvider.getID() + '_search_mode',
                                                                   'eponly')
            if hasattr(curTorrentProvider, 'search_fallback'):
                curTorrentProvider.search_fallback = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                            curTorrentProvider.getID() + '_search_fallback',
                                                                            0))

            if hasattr(curTorrentProvider, 'enable_daily'):
                curTorrentProvider.enable_daily = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                         curTorrentProvider.getID() + '_enable_daily',
                                                                         1))

            if hasattr(curTorrentProvider, 'enable_backlog'):
                curTorrentProvider.enable_backlog = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                           curTorrentProvider.getID() + '_enable_backlog',
                                                                           curTorrentProvider.supportsBacklog))

            if hasattr(curTorrentProvider, 'cat'):
                curTorrentProvider.cat = check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                           curTorrentProvider.getID() + '_cat', 0)
            if hasattr(curTorrentProvider, 'subtitle'):
                curTorrentProvider.subtitle = bool(check_setting_int(CFG, curTorrentProvider.getID().upper(),
                                                                     curTorrentProvider.getID() + '_subtitle', 0))

        for curNzbProvider in [curProvider for curProvider in providers.sortedProviderList() if
                               curProvider.providerType == GenericProvider.NZB]:
            curNzbProvider.enabled = bool(
                check_setting_int(CFG, curNzbProvider.getID().upper(), curNzbProvider.getID(), 0))
            if hasattr(curNzbProvider, 'api_key'):
                curNzbProvider.api_key = check_setting_str(CFG, curNzbProvider.getID().upper(),
                                                           curNzbProvider.getID() + '_api_key', '', censor_log=True)
            if hasattr(curNzbProvider, 'username'):
                curNzbProvider.username = check_setting_str(CFG, curNzbProvider.getID().upper(),
                                                            curNzbProvider.getID() + '_username', '', censor_log=True)
            if hasattr(curNzbProvider, 'search_mode'):
                curNzbProvider.search_mode = check_setting_str(CFG, curNzbProvider.getID().upper(),
                                                               curNzbProvider.getID() + '_search_mode',
                                                               'eponly')
            if hasattr(curNzbProvider, 'search_fallback'):
                curNzbProvider.search_fallback = bool(check_setting_int(CFG, curNzbProvider.getID().upper(),
                                                                        curNzbProvider.getID() + '_search_fallback',
                                                                        0))
            if hasattr(curNzbProvider, 'enable_daily'):
                curNzbProvider.enable_daily = bool(check_setting_int(CFG, curNzbProvider.getID().upper(),
                                                                     curNzbProvider.getID() + '_enable_daily',
                                                                     1))

            if hasattr(curNzbProvider, 'enable_backlog'):
                curNzbProvider.enable_backlog = bool(check_setting_int(CFG, curNzbProvider.getID().upper(),
                                                                       curNzbProvider.getID() + '_enable_backlog',
                                                                       curNzbProvider.supportsBacklog))

        if not os.path.isfile(CONFIG_FILE):
            logger.log(u"Unable to find '" + CONFIG_FILE + "', all settings will be default!", logger.DEBUG)
            save_config()

        # initialize the main SB database
        myDB = db.DBConnection()
        db.upgradeDatabase(myDB, mainDB.InitialSchema)

        # initialize the cache database
        myDB = db.DBConnection('cache.db')
        db.upgradeDatabase(myDB, cache_db.InitialSchema)

        # initialize the failed downloads database
        myDB = db.DBConnection('failed.db')
        db.upgradeDatabase(myDB, failed_db.InitialSchema)

        # fix up any db problems
        myDB = db.DBConnection()
        db.sanityCheckDatabase(myDB, mainDB.MainSanityCheck)

        # migrate the config if it needs it
        migrator = ConfigMigrator(CFG)
        migrator.migrate_config()

        # initialize metadata_providers
        metadata_provider_dict = metadata.get_metadata_generator_dict()
        for cur_metadata_tuple in [(METADATA_KODI, metadata.kodi),
                                   (METADATA_KODI_12PLUS, metadata.kodi_12plus),
                                   (METADATA_MEDIABROWSER, metadata.mediabrowser),
                                   (METADATA_PS3, metadata.ps3),
                                   (METADATA_WDTV, metadata.wdtv),
                                   (METADATA_TIVO, metadata.tivo),
                                   (METADATA_MEDE8ER, metadata.mede8er)]:

            (cur_metadata_config, cur_metadata_class) = cur_metadata_tuple
            tmp_provider = cur_metadata_class.metadata_class()
            tmp_provider.set_config(cur_metadata_config)
            metadata_provider_dict[tmp_provider.name] = tmp_provider

        # initialize schedulers
        # updaters
        versionCheckScheduler = scheduler.Scheduler(versionChecker.CheckVersion(),
                                                    cycleTime=datetime.timedelta(hours=UPDATE_FREQUENCY),
                                                    threadName="CHECKVERSION",
                                                    silent=False)

        showQueueScheduler = scheduler.Scheduler(show_queue.ShowQueue(),
                                                 cycleTime=datetime.timedelta(seconds=3),
                                                 threadName="SHOWQUEUE")

        showUpdateScheduler = scheduler.Scheduler(showUpdater.ShowUpdater(),
                                                  cycleTime=datetime.timedelta(hours=1),
                                                  threadName="SHOWUPDATER",
                                                  start_time=datetime.time(hour=SHOWUPDATE_HOUR))

        # searchers
        searchQueueScheduler = scheduler.Scheduler(search_queue.SearchQueue(),
                                                   cycleTime=datetime.timedelta(seconds=3),
                                                   threadName="SEARCHQUEUE")

        # TODO: update_interval should take last daily/backlog times into account!
        update_interval = datetime.timedelta(minutes=DAILYSEARCH_FREQUENCY)
        dailySearchScheduler = scheduler.Scheduler(dailysearcher.DailySearcher(),
                                                   cycleTime=update_interval,
                                                   threadName="DAILYSEARCHER",
                                                   run_delay=update_interval)

        update_interval = datetime.timedelta(minutes=BACKLOG_FREQUENCY)
        backlogSearchScheduler = searchBacklog.BacklogSearchScheduler(searchBacklog.BacklogSearcher(),
                                                                      cycleTime=update_interval,
                                                                      threadName="BACKLOG",
                                                                      run_delay=update_interval)

        search_intervals = {'15m': 15, '45m': 45, '90m': 90, '4h': 4 * 60, 'daily': 24 * 60}
        if CHECK_PROPERS_INTERVAL in search_intervals:
            update_interval = datetime.timedelta(minutes=search_intervals[CHECK_PROPERS_INTERVAL])
            run_at = None
        else:
            update_interval = datetime.timedelta(hours=1)
            run_at = datetime.time(hour=1)  # 1 AM

        properFinderScheduler = scheduler.Scheduler(properFinder.ProperFinder(),
                                                    cycleTime=update_interval,
                                                    threadName="FINDPROPERS",
                                                    start_time=run_at,
                                                    run_delay=update_interval)

        # processors
        autoPostProcesserScheduler = scheduler.Scheduler(autoPostProcesser.PostProcesser(),
                                                         cycleTime=datetime.timedelta(
                                                             minutes=AUTOPOSTPROCESSER_FREQUENCY),
                                                         threadName="POSTPROCESSER",
                                                         silent=not PROCESS_AUTOMATICALLY)

        traktCheckerScheduler = scheduler.Scheduler(traktChecker.TraktChecker(),
                                                    cycleTime=datetime.timedelta(hours=1),
                                                    threadName="TRAKTCHECKER",
                                                    silent=not USE_TRAKT)

        subtitlesFinderScheduler = scheduler.Scheduler(subtitles.SubtitlesFinder(),
                                                       cycleTime=datetime.timedelta(hours=SUBTITLES_FINDER_FREQUENCY),
                                                       threadName="FINDSUBTITLES",
                                                       silent=not USE_SUBTITLES)

        showList = []
        loadingShowList = {}

        __INITIALIZED__ = True
        return True


def start():
    global started

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
            if DOWNLOAD_PROPERS:
                properFinderScheduler.silent = False
                properFinderScheduler.enable = True
            else:
                properFinderScheduler.enable = False
                properFinderScheduler.silent = True
            properFinderScheduler.start()

            # start the post processor
            if PROCESS_AUTOMATICALLY:
                autoPostProcesserScheduler.silent = False
                autoPostProcesserScheduler.enable = True
            else:
                autoPostProcesserScheduler.enable = False
                autoPostProcesserScheduler.silent = True
            autoPostProcesserScheduler.start()

            # start the subtitles finder
            if USE_SUBTITLES:
                subtitlesFinderScheduler.silent = False
                subtitlesFinderScheduler.enable = True
            else:
                subtitlesFinderScheduler.enable = False
                subtitlesFinderScheduler.silent = True
            subtitlesFinderScheduler.start()

            # start the trakt checker
            if USE_TRAKT:
                traktCheckerScheduler.silent = False
                traktCheckerScheduler.enable = True
            else:
                traktCheckerScheduler.enable = False
                traktCheckerScheduler.silent = True
            traktCheckerScheduler.start()

            started = True


def halt():
    global __INITIALIZED__, started

    with INIT_LOCK:

        if __INITIALIZED__:

            logger.log(u"Aborting all threads")

            events.stop.set()
            logger.log(u"Waiting for the EVENTS thread to exit")
            try:
                events.join(10)
            except Exception:
                pass

            dailySearchScheduler.stop.set()
            logger.log(u"Waiting for the DAILYSEARCH thread to exit")
            try:
                dailySearchScheduler.join(10)
            except Exception:
                pass

            backlogSearchScheduler.stop.set()
            logger.log(u"Waiting for the BACKLOG thread to exit")
            try:
                backlogSearchScheduler.join(10)
            except Exception:
                pass

            showUpdateScheduler.stop.set()
            logger.log(u"Waiting for the SHOWUPDATER thread to exit")
            try:
                showUpdateScheduler.join(10)
            except Exception:
                pass

            versionCheckScheduler.stop.set()
            logger.log(u"Waiting for the VERSIONCHECKER thread to exit")
            try:
                versionCheckScheduler.join(10)
            except Exception:
                pass

            showQueueScheduler.stop.set()
            logger.log(u"Waiting for the SHOWQUEUE thread to exit")
            try:
                showQueueScheduler.join(10)
            except Exception:
                pass

            searchQueueScheduler.stop.set()
            logger.log(u"Waiting for the SEARCHQUEUE thread to exit")
            try:
                searchQueueScheduler.join(10)
            except Exception:
                pass

            autoPostProcesserScheduler.stop.set()
            logger.log(u"Waiting for the POSTPROCESSER thread to exit")
            try:
                autoPostProcesserScheduler.join(10)
            except Exception:
                pass

            traktCheckerScheduler.stop.set()
            logger.log(u"Waiting for the TRAKTCHECKER thread to exit")
            try:
                traktCheckerScheduler.join(10)
            except Exception:
                pass

            properFinderScheduler.stop.set()
            logger.log(u"Waiting for the PROPERFINDER thread to exit")
            try:
                properFinderScheduler.join(10)
            except Exception:
                pass

            subtitlesFinderScheduler.stop.set()
            logger.log(u"Waiting for the SUBTITLESFINDER thread to exit")
            try:
                subtitlesFinderScheduler.join(10)
            except Exception:
                pass

            if ADBA_CONNECTION:
                ADBA_CONNECTION.logout()
                logger.log(u"Waiting for the ANIDB CONNECTION thread to exit")
                try:
                    ADBA_CONNECTION.join(10)
                except Exception:
                    pass

            __INITIALIZED__ = False
            started = False


def sig_handler(signum=None, frame=None):
    if not isinstance(signum, type(None)):
        logger.log(u"Signal %i caught, saving and exiting..." % int(signum))
        Shutdown.stop(PID)


def saveAll():
    # write all shows
    logger.log(u"Saving all shows to the database")
    for show in showList:
        show.saveToDB()

    # save config
    logger.log(u"Saving config file to disk")
    save_config()


def restart(soft=True):
    if soft:
        halt()
        saveAll()
        logger.log(u"Re-initializing all data")
        initialize()
    else:
        events.put(events.SystemEvent.RESTART)


def save_config():
    new_config = ConfigObj()
    new_config.filename = CONFIG_FILE

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    new_config['General'] = {}
    new_config['General']['git_autoissues'] = int(GIT_AUTOISSUES)
    new_config['General']['git_username'] = GIT_USERNAME
    new_config['General']['git_password'] = helpers.encrypt(GIT_PASSWORD, ENCRYPTION_VERSION)
    new_config['General']['git_reset'] = int(GIT_RESET)
    new_config['General']['branch'] = BRANCH
    new_config['General']['git_remote'] = GIT_REMOTE
    new_config['General']['git_remote_url'] = GIT_REMOTE_URL
    new_config['General']['cur_commit_hash'] = CUR_COMMIT_HASH
    new_config['General']['cur_commit_branch'] = CUR_COMMIT_BRANCH
    new_config['General']['git_newver'] = int(GIT_NEWVER)
    new_config['General']['config_version'] = CONFIG_VERSION
    new_config['General']['encryption_version'] = int(ENCRYPTION_VERSION)
    new_config['General']['encryption_secret'] = ENCRYPTION_SECRET
    new_config['General']['log_dir'] = ACTUAL_LOG_DIR if ACTUAL_LOG_DIR else 'Logs'
    new_config['General']['log_nr'] = int(LOG_NR)
    new_config['General']['log_size'] = int(LOG_SIZE)
    new_config['General']['socket_timeout'] = SOCKET_TIMEOUT
    new_config['General']['web_port'] = WEB_PORT
    new_config['General']['web_host'] = WEB_HOST
    new_config['General']['web_ipv6'] = int(WEB_IPV6)
    new_config['General']['web_log'] = int(WEB_LOG)
    new_config['General']['web_root'] = WEB_ROOT
    new_config['General']['web_username'] = WEB_USERNAME
    new_config['General']['web_password'] = helpers.encrypt(WEB_PASSWORD, ENCRYPTION_VERSION)
    new_config['General']['web_cookie_secret'] = WEB_COOKIE_SECRET
    new_config['General']['web_use_gzip'] = int(WEB_USE_GZIP)
    new_config['General']['ssl_verify'] = int(SSL_VERIFY)
    new_config['General']['download_url'] = DOWNLOAD_URL
    new_config['General']['localhost_ip'] = LOCALHOST_IP
    new_config['General']['cpu_preset'] = CPU_PRESET
    new_config['General']['anon_redirect'] = ANON_REDIRECT
    new_config['General']['api_key'] = API_KEY
    new_config['General']['debug'] = int(DEBUG)
    new_config['General']['default_page'] = DEFAULT_PAGE
    new_config['General']['enable_https'] = int(ENABLE_HTTPS)
    new_config['General']['https_cert'] = HTTPS_CERT
    new_config['General']['https_key'] = HTTPS_KEY
    new_config['General']['handle_reverse_proxy'] = int(HANDLE_REVERSE_PROXY)
    new_config['General']['use_nzbs'] = int(USE_NZBS)
    new_config['General']['use_torrents'] = int(USE_TORRENTS)
    new_config['General']['nzb_method'] = NZB_METHOD
    new_config['General']['torrent_method'] = TORRENT_METHOD
    new_config['General']['usenet_retention'] = int(USENET_RETENTION)
    new_config['General']['autopostprocesser_frequency'] = int(AUTOPOSTPROCESSER_FREQUENCY)
    new_config['General']['dailysearch_frequency'] = int(DAILYSEARCH_FREQUENCY)
    new_config['General']['backlog_frequency'] = int(BACKLOG_FREQUENCY)
    new_config['General']['update_frequency'] = int(UPDATE_FREQUENCY)
    new_config['General']['showupdate_hour'] = int(SHOWUPDATE_HOUR)
    new_config['General']['download_propers'] = int(DOWNLOAD_PROPERS)
    new_config['General']['randomize_providers'] = int(RANDOMIZE_PROVIDERS)
    new_config['General']['check_propers_interval'] = CHECK_PROPERS_INTERVAL
    new_config['General']['allow_high_priority'] = int(ALLOW_HIGH_PRIORITY)
    new_config['General']['skip_removed_files'] = int(SKIP_REMOVED_FILES)
    new_config['General']['quality_default'] = int(QUALITY_DEFAULT)
    new_config['General']['status_default'] = int(STATUS_DEFAULT)
    new_config['General']['status_default_after'] = int(STATUS_DEFAULT_AFTER)
    new_config['General']['flatten_folders_default'] = int(FLATTEN_FOLDERS_DEFAULT)
    new_config['General']['indexer_default'] = int(INDEXER_DEFAULT)
    new_config['General']['indexer_timeout'] = int(INDEXER_TIMEOUT)
    new_config['General']['anime_default'] = int(ANIME_DEFAULT)
    new_config['General']['scene_default'] = int(SCENE_DEFAULT)
    new_config['General']['archive_default'] = int(ARCHIVE_DEFAULT)
    new_config['General']['provider_order'] = ' '.join(PROVIDER_ORDER)
    new_config['General']['version_notify'] = int(VERSION_NOTIFY)
    new_config['General']['auto_update'] = int(AUTO_UPDATE)
    new_config['General']['notify_on_update'] = int(NOTIFY_ON_UPDATE)
    new_config['General']['naming_strip_year'] = int(NAMING_STRIP_YEAR)
    new_config['General']['naming_pattern'] = NAMING_PATTERN
    new_config['General']['naming_custom_abd'] = int(NAMING_CUSTOM_ABD)
    new_config['General']['naming_abd_pattern'] = NAMING_ABD_PATTERN
    new_config['General']['naming_custom_sports'] = int(NAMING_CUSTOM_SPORTS)
    new_config['General']['naming_sports_pattern'] = NAMING_SPORTS_PATTERN
    new_config['General']['naming_custom_anime'] = int(NAMING_CUSTOM_ANIME)
    new_config['General']['naming_anime_pattern'] = NAMING_ANIME_PATTERN
    new_config['General']['naming_multi_ep'] = int(NAMING_MULTI_EP)
    new_config['General']['naming_anime_multi_ep'] = int(NAMING_ANIME_MULTI_EP)
    new_config['General']['naming_anime'] = int(NAMING_ANIME)
    new_config['General']['indexerDefaultLang'] = INDEXER_DEFAULT_LANGUAGE
    new_config['General']['ep_default_deleted_status'] = int(EP_DEFAULT_DELETED_STATUS)
    new_config['General']['launch_browser'] = int(LAUNCH_BROWSER)
    new_config['General']['trash_remove_show'] = int(TRASH_REMOVE_SHOW)
    new_config['General']['trash_rotate_logs'] = int(TRASH_ROTATE_LOGS)
    new_config['General']['sort_article'] = int(SORT_ARTICLE)
    new_config['General']['proxy_setting'] = PROXY_SETTING
    new_config['General']['proxy_indexers'] = int(PROXY_INDEXERS)

    new_config['General']['use_listview'] = int(USE_LISTVIEW)
    new_config['General']['metadata_kodi'] = METADATA_KODI
    new_config['General']['metadata_kodi_12plus'] = METADATA_KODI_12PLUS
    new_config['General']['metadata_mediabrowser'] = METADATA_MEDIABROWSER
    new_config['General']['metadata_ps3'] = METADATA_PS3
    new_config['General']['metadata_wdtv'] = METADATA_WDTV
    new_config['General']['metadata_tivo'] = METADATA_TIVO
    new_config['General']['metadata_mede8er'] = METADATA_MEDE8ER

    new_config['General']['backlog_days'] = int(BACKLOG_DAYS)

    new_config['General']['cache_dir'] = ACTUAL_CACHE_DIR if ACTUAL_CACHE_DIR else 'cache'
    new_config['General']['root_dirs'] = ROOT_DIRS if ROOT_DIRS else ''
    new_config['General']['tv_download_dir'] = TV_DOWNLOAD_DIR
    new_config['General']['keep_processed_dir'] = int(KEEP_PROCESSED_DIR)
    new_config['General']['process_method'] = PROCESS_METHOD
    new_config['General']['del_rar_contents'] = int(DELRARCONTENTS)
    new_config['General']['move_associated_files'] = int(MOVE_ASSOCIATED_FILES)
    new_config['General']['sync_files'] = SYNC_FILES
    new_config['General']['postpone_if_sync_files'] = int(POSTPONE_IF_SYNC_FILES)
    new_config['General']['nfo_rename'] = int(NFO_RENAME)
    new_config['General']['process_automatically'] = int(PROCESS_AUTOMATICALLY)
    new_config['General']['no_delete'] = int(NO_DELETE)
    new_config['General']['unpack'] = int(UNPACK)
    new_config['General']['rename_episodes'] = int(RENAME_EPISODES)
    new_config['General']['airdate_episodes'] = int(AIRDATE_EPISODES)
    new_config['General']['file_timestamp_timezone'] = FILE_TIMESTAMP_TIMEZONE
    new_config['General']['create_missing_show_dirs'] = int(CREATE_MISSING_SHOW_DIRS)
    new_config['General']['add_shows_wo_dir'] = int(ADD_SHOWS_WO_DIR)

    new_config['General']['extra_scripts'] = '|'.join(EXTRA_SCRIPTS)
    new_config['General']['git_path'] = GIT_PATH
    new_config['General']['ignore_words'] = IGNORE_WORDS
    new_config['General']['require_words'] = REQUIRE_WORDS
    new_config['General']['ignored_subs_list'] = IGNORED_SUBS_LIST
    new_config['General']['calendar_unprotected'] = int(CALENDAR_UNPROTECTED)
    new_config['General']['calendar_icons'] = int(CALENDAR_ICONS)
    new_config['General']['no_restart'] = int(NO_RESTART)
    new_config['General']['developer'] = int(DEVELOPER)
    new_config['General']['display_all_seasons'] = int(DISPLAY_ALL_SEASONS)
    new_config['General']['news_last_read'] = NEWS_LAST_READ

    new_config['Blackhole'] = {}
    new_config['Blackhole']['nzb_dir'] = NZB_DIR
    new_config['Blackhole']['torrent_dir'] = TORRENT_DIR

    # dynamically save provider settings
    for curTorrentProvider in [curProvider for curProvider in providers.sortedProviderList() if
                               curProvider.providerType == GenericProvider.TORRENT]:
        new_config[curTorrentProvider.getID().upper()] = {}
        new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID()] = int(curTorrentProvider.enabled)
        if hasattr(curTorrentProvider, 'digest'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_digest'] = curTorrentProvider.digest
        if hasattr(curTorrentProvider, 'hash'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_hash'] = curTorrentProvider.hash
        if hasattr(curTorrentProvider, 'api_key'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_api_key'] = curTorrentProvider.api_key
        if hasattr(curTorrentProvider, 'username'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_username'] = curTorrentProvider.username
        if hasattr(curTorrentProvider, 'password'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_password'] = helpers.encrypt(
                curTorrentProvider.password, ENCRYPTION_VERSION)
        if hasattr(curTorrentProvider, 'passkey'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_passkey'] = curTorrentProvider.passkey
        if hasattr(curTorrentProvider, 'pin'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_pin'] = curTorrentProvider.pin
        if hasattr(curTorrentProvider, 'confirmed'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_confirmed'] = int(
                curTorrentProvider.confirmed)
        if hasattr(curTorrentProvider, 'ranked'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_ranked'] = int(
                curTorrentProvider.ranked)
        if hasattr(curTorrentProvider, 'engrelease'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_engrelease'] = int(
                curTorrentProvider.engrelease)
        if hasattr(curTorrentProvider, 'onlyspasearch'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_onlyspasearch'] = int(
                curTorrentProvider.onlyspasearch)
        if hasattr(curTorrentProvider, 'sorting'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_sorting'] = curTorrentProvider.sorting
        if hasattr(curTorrentProvider, 'ratio'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_ratio'] = curTorrentProvider.ratio
        if hasattr(curTorrentProvider, 'minseed'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_minseed'] = int(
                curTorrentProvider.minseed)
        if hasattr(curTorrentProvider, 'minleech'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_minleech'] = int(
                curTorrentProvider.minleech)
        if hasattr(curTorrentProvider, 'options'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_options'] = curTorrentProvider.options
        if hasattr(curTorrentProvider, 'freeleech'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_freeleech'] = int(
                curTorrentProvider.freeleech)
        if hasattr(curTorrentProvider, 'search_mode'):
            new_config[curTorrentProvider.getID().upper()][
                curTorrentProvider.getID() + '_search_mode'] = curTorrentProvider.search_mode
        if hasattr(curTorrentProvider, 'search_fallback'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_search_fallback'] = int(
                curTorrentProvider.search_fallback)
        if hasattr(curTorrentProvider, 'enable_daily'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_enable_daily'] = int(
                curTorrentProvider.enable_daily)
        if hasattr(curTorrentProvider, 'enable_backlog'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_enable_backlog'] = int(
                curTorrentProvider.enable_backlog)
        if hasattr(curTorrentProvider, 'cat'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_cat'] = int(
                curTorrentProvider.cat)
        if hasattr(curTorrentProvider, 'subtitle'):
            new_config[curTorrentProvider.getID().upper()][curTorrentProvider.getID() + '_subtitle'] = int(
                curTorrentProvider.subtitle)

    for curNzbProvider in [curProvider for curProvider in providers.sortedProviderList() if
                           curProvider.providerType == GenericProvider.NZB]:
        new_config[curNzbProvider.getID().upper()] = {}
        new_config[curNzbProvider.getID().upper()][curNzbProvider.getID()] = int(curNzbProvider.enabled)

        if hasattr(curNzbProvider, 'api_key'):
            new_config[curNzbProvider.getID().upper()][
                curNzbProvider.getID() + '_api_key'] = curNzbProvider.api_key
        if hasattr(curNzbProvider, 'username'):
            new_config[curNzbProvider.getID().upper()][
                curNzbProvider.getID() + '_username'] = curNzbProvider.username
        if hasattr(curNzbProvider, 'search_mode'):
            new_config[curNzbProvider.getID().upper()][
                curNzbProvider.getID() + '_search_mode'] = curNzbProvider.search_mode
        if hasattr(curNzbProvider, 'search_fallback'):
            new_config[curNzbProvider.getID().upper()][curNzbProvider.getID() + '_search_fallback'] = int(
                curNzbProvider.search_fallback)
        if hasattr(curNzbProvider, 'enable_daily'):
            new_config[curNzbProvider.getID().upper()][curNzbProvider.getID() + '_enable_daily'] = int(
                curNzbProvider.enable_daily)
        if hasattr(curNzbProvider, 'enable_backlog'):
            new_config[curNzbProvider.getID().upper()][curNzbProvider.getID() + '_enable_backlog'] = int(
                curNzbProvider.enable_backlog)

    new_config['NZBs'] = {}
    new_config['NZBs']['nzbs'] = int(NZBS)
    new_config['NZBs']['nzbs_uid'] = NZBS_UID
    new_config['NZBs']['nzbs_hash'] = NZBS_HASH

    new_config['Newzbin'] = {}
    new_config['Newzbin']['newzbin'] = int(NEWZBIN)
    new_config['Newzbin']['newzbin_username'] = NEWZBIN_USERNAME
    new_config['Newzbin']['newzbin_password'] = helpers.encrypt(NEWZBIN_PASSWORD, ENCRYPTION_VERSION)

    new_config['SABnzbd'] = {}
    new_config['SABnzbd']['sab_username'] = SAB_USERNAME
    new_config['SABnzbd']['sab_password'] = helpers.encrypt(SAB_PASSWORD, ENCRYPTION_VERSION)
    new_config['SABnzbd']['sab_apikey'] = SAB_APIKEY
    new_config['SABnzbd']['sab_category'] = SAB_CATEGORY
    new_config['SABnzbd']['sab_category_backlog'] = SAB_CATEGORY_BACKLOG
    new_config['SABnzbd']['sab_category_anime'] = SAB_CATEGORY_ANIME
    new_config['SABnzbd']['sab_category_anime_backlog'] = SAB_CATEGORY_ANIME_BACKLOG
    new_config['SABnzbd']['sab_host'] = SAB_HOST
    new_config['SABnzbd']['sab_forced'] = int(SAB_FORCED)

    new_config['NZBget'] = {}

    new_config['NZBget']['nzbget_username'] = NZBGET_USERNAME
    new_config['NZBget']['nzbget_password'] = helpers.encrypt(NZBGET_PASSWORD, ENCRYPTION_VERSION)
    new_config['NZBget']['nzbget_category'] = NZBGET_CATEGORY
    new_config['NZBget']['nzbget_category_backlog'] = NZBGET_CATEGORY_BACKLOG
    new_config['NZBget']['nzbget_category_anime'] = NZBGET_CATEGORY_ANIME
    new_config['NZBget']['nzbget_category_anime_backlog'] = NZBGET_CATEGORY_ANIME_BACKLOG
    new_config['NZBget']['nzbget_host'] = NZBGET_HOST
    new_config['NZBget']['nzbget_use_https'] = int(NZBGET_USE_HTTPS)
    new_config['NZBget']['nzbget_priority'] = NZBGET_PRIORITY

    new_config['TORRENT'] = {}
    new_config['TORRENT']['torrent_username'] = TORRENT_USERNAME
    new_config['TORRENT']['torrent_password'] = helpers.encrypt(TORRENT_PASSWORD, ENCRYPTION_VERSION)
    new_config['TORRENT']['torrent_host'] = TORRENT_HOST
    new_config['TORRENT']['torrent_path'] = TORRENT_PATH
    new_config['TORRENT']['torrent_seed_time'] = int(TORRENT_SEED_TIME)
    new_config['TORRENT']['torrent_paused'] = int(TORRENT_PAUSED)
    new_config['TORRENT']['torrent_high_bandwidth'] = int(TORRENT_HIGH_BANDWIDTH)
    new_config['TORRENT']['torrent_label'] = TORRENT_LABEL
    new_config['TORRENT']['torrent_label_anime'] = TORRENT_LABEL_ANIME
    new_config['TORRENT']['torrent_verify_cert'] = int(TORRENT_VERIFY_CERT)
    new_config['TORRENT']['torrent_rpcurl'] = TORRENT_RPCURL
    new_config['TORRENT']['torrent_auth_type'] = TORRENT_AUTH_TYPE

    new_config['KODI'] = {}
    new_config['KODI']['use_kodi'] = int(USE_KODI)
    new_config['KODI']['kodi_always_on'] = int(KODI_ALWAYS_ON)
    new_config['KODI']['kodi_notify_onsnatch'] = int(KODI_NOTIFY_ONSNATCH)
    new_config['KODI']['kodi_notify_ondownload'] = int(KODI_NOTIFY_ONDOWNLOAD)
    new_config['KODI']['kodi_notify_onsubtitledownload'] = int(KODI_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['KODI']['kodi_update_library'] = int(KODI_UPDATE_LIBRARY)
    new_config['KODI']['kodi_update_full'] = int(KODI_UPDATE_FULL)
    new_config['KODI']['kodi_update_onlyfirst'] = int(KODI_UPDATE_ONLYFIRST)
    new_config['KODI']['kodi_host'] = KODI_HOST
    new_config['KODI']['kodi_username'] = KODI_USERNAME
    new_config['KODI']['kodi_password'] = helpers.encrypt(KODI_PASSWORD, ENCRYPTION_VERSION)

    new_config['Plex'] = {}
    new_config['Plex']['use_plex'] = int(USE_PLEX)
    new_config['Plex']['plex_notify_onsnatch'] = int(PLEX_NOTIFY_ONSNATCH)
    new_config['Plex']['plex_notify_ondownload'] = int(PLEX_NOTIFY_ONDOWNLOAD)
    new_config['Plex']['plex_notify_onsubtitledownload'] = int(PLEX_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Plex']['plex_update_library'] = int(PLEX_UPDATE_LIBRARY)
    new_config['Plex']['plex_server_host'] = PLEX_SERVER_HOST
    new_config['Plex']['plex_server_token'] = PLEX_SERVER_TOKEN
    new_config['Plex']['plex_host'] = PLEX_HOST
    new_config['Plex']['plex_username'] = PLEX_USERNAME
    new_config['Plex']['plex_password'] = helpers.encrypt(PLEX_PASSWORD, ENCRYPTION_VERSION)

    new_config['Emby'] = {}
    new_config['Emby']['use_emby'] = int(USE_EMBY)
    new_config['Emby']['emby_host'] = EMBY_HOST
    new_config['Emby']['emby_apikey'] = EMBY_APIKEY

    new_config['Growl'] = {}
    new_config['Growl']['use_growl'] = int(USE_GROWL)
    new_config['Growl']['growl_notify_onsnatch'] = int(GROWL_NOTIFY_ONSNATCH)
    new_config['Growl']['growl_notify_ondownload'] = int(GROWL_NOTIFY_ONDOWNLOAD)
    new_config['Growl']['growl_notify_onsubtitledownload'] = int(GROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Growl']['growl_host'] = GROWL_HOST
    new_config['Growl']['growl_password'] = helpers.encrypt(GROWL_PASSWORD, ENCRYPTION_VERSION)

    new_config['FreeMobile'] = {}
    new_config['FreeMobile']['use_freemobile'] = int(USE_FREEMOBILE)
    new_config['FreeMobile']['freemobile_notify_onsnatch'] = int(FREEMOBILE_NOTIFY_ONSNATCH)
    new_config['FreeMobile']['freemobile_notify_ondownload'] = int(FREEMOBILE_NOTIFY_ONDOWNLOAD)
    new_config['FreeMobile']['freemobile_notify_onsubtitledownload'] = int(FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['FreeMobile']['freemobile_id'] = FREEMOBILE_ID
    new_config['FreeMobile']['freemobile_apikey'] = FREEMOBILE_APIKEY

    new_config['Prowl'] = {}
    new_config['Prowl']['use_prowl'] = int(USE_PROWL)
    new_config['Prowl']['prowl_notify_onsnatch'] = int(PROWL_NOTIFY_ONSNATCH)
    new_config['Prowl']['prowl_notify_ondownload'] = int(PROWL_NOTIFY_ONDOWNLOAD)
    new_config['Prowl']['prowl_notify_onsubtitledownload'] = int(PROWL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Prowl']['prowl_api'] = PROWL_API
    new_config['Prowl']['prowl_priority'] = PROWL_PRIORITY

    new_config['Twitter'] = {}
    new_config['Twitter']['use_twitter'] = int(USE_TWITTER)
    new_config['Twitter']['twitter_notify_onsnatch'] = int(TWITTER_NOTIFY_ONSNATCH)
    new_config['Twitter']['twitter_notify_ondownload'] = int(TWITTER_NOTIFY_ONDOWNLOAD)
    new_config['Twitter']['twitter_notify_onsubtitledownload'] = int(TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Twitter']['twitter_username'] = TWITTER_USERNAME
    new_config['Twitter']['twitter_password'] = helpers.encrypt(TWITTER_PASSWORD, ENCRYPTION_VERSION)
    new_config['Twitter']['twitter_prefix'] = TWITTER_PREFIX
    new_config['Twitter']['twitter_dmto'] = TWITTER_DMTO
    new_config['Twitter']['twitter_usedm'] = int(TWITTER_USEDM)

    new_config['Boxcar'] = {}
    new_config['Boxcar']['use_boxcar'] = int(USE_BOXCAR)
    new_config['Boxcar']['boxcar_notify_onsnatch'] = int(BOXCAR_NOTIFY_ONSNATCH)
    new_config['Boxcar']['boxcar_notify_ondownload'] = int(BOXCAR_NOTIFY_ONDOWNLOAD)
    new_config['Boxcar']['boxcar_notify_onsubtitledownload'] = int(BOXCAR_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Boxcar']['boxcar_username'] = BOXCAR_USERNAME

    new_config['Boxcar2'] = {}
    new_config['Boxcar2']['use_boxcar2'] = int(USE_BOXCAR2)
    new_config['Boxcar2']['boxcar2_notify_onsnatch'] = int(BOXCAR2_NOTIFY_ONSNATCH)
    new_config['Boxcar2']['boxcar2_notify_ondownload'] = int(BOXCAR2_NOTIFY_ONDOWNLOAD)
    new_config['Boxcar2']['boxcar2_notify_onsubtitledownload'] = int(BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Boxcar2']['boxcar2_accesstoken'] = BOXCAR2_ACCESSTOKEN

    new_config['Pushover'] = {}
    new_config['Pushover']['use_pushover'] = int(USE_PUSHOVER)
    new_config['Pushover']['pushover_notify_onsnatch'] = int(PUSHOVER_NOTIFY_ONSNATCH)
    new_config['Pushover']['pushover_notify_ondownload'] = int(PUSHOVER_NOTIFY_ONDOWNLOAD)
    new_config['Pushover']['pushover_notify_onsubtitledownload'] = int(PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Pushover']['pushover_userkey'] = PUSHOVER_USERKEY
    new_config['Pushover']['pushover_apikey'] = PUSHOVER_APIKEY
    new_config['Pushover']['pushover_device'] = PUSHOVER_DEVICE
    new_config['Pushover']['pushover_sound'] = PUSHOVER_SOUND

    new_config['Libnotify'] = {}
    new_config['Libnotify']['use_libnotify'] = int(USE_LIBNOTIFY)
    new_config['Libnotify']['libnotify_notify_onsnatch'] = int(LIBNOTIFY_NOTIFY_ONSNATCH)
    new_config['Libnotify']['libnotify_notify_ondownload'] = int(LIBNOTIFY_NOTIFY_ONDOWNLOAD)
    new_config['Libnotify']['libnotify_notify_onsubtitledownload'] = int(LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD)

    new_config['NMJ'] = {}
    new_config['NMJ']['use_nmj'] = int(USE_NMJ)
    new_config['NMJ']['nmj_host'] = NMJ_HOST
    new_config['NMJ']['nmj_database'] = NMJ_DATABASE
    new_config['NMJ']['nmj_mount'] = NMJ_MOUNT

    new_config['NMJv2'] = {}
    new_config['NMJv2']['use_nmjv2'] = int(USE_NMJv2)
    new_config['NMJv2']['nmjv2_host'] = NMJv2_HOST
    new_config['NMJv2']['nmjv2_database'] = NMJv2_DATABASE
    new_config['NMJv2']['nmjv2_dbloc'] = NMJv2_DBLOC

    new_config['Synology'] = {}
    new_config['Synology']['use_synoindex'] = int(USE_SYNOINDEX)

    new_config['SynologyNotifier'] = {}
    new_config['SynologyNotifier']['use_synologynotifier'] = int(USE_SYNOLOGYNOTIFIER)
    new_config['SynologyNotifier']['synologynotifier_notify_onsnatch'] = int(SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH)
    new_config['SynologyNotifier']['synologynotifier_notify_ondownload'] = int(SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD)
    new_config['SynologyNotifier']['synologynotifier_notify_onsubtitledownload'] = int(
        SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)

    new_config['Trakt'] = {}
    new_config['Trakt']['use_trakt'] = int(USE_TRAKT)
    new_config['Trakt']['trakt_username'] = TRAKT_USERNAME
    new_config['Trakt']['trakt_access_token'] = TRAKT_ACCESS_TOKEN
    new_config['Trakt']['trakt_refresh_token'] = TRAKT_REFRESH_TOKEN
    new_config['Trakt']['trakt_remove_watchlist'] = int(TRAKT_REMOVE_WATCHLIST)
    new_config['Trakt']['trakt_remove_serieslist'] = int(TRAKT_REMOVE_SERIESLIST)
    new_config['Trakt']['trakt_remove_show_from_sickrage'] = int(TRAKT_REMOVE_SHOW_FROM_SICKRAGE)
    new_config['Trakt']['trakt_sync_watchlist'] = int(TRAKT_SYNC_WATCHLIST)
    new_config['Trakt']['trakt_method_add'] = int(TRAKT_METHOD_ADD)
    new_config['Trakt']['trakt_start_paused'] = int(TRAKT_START_PAUSED)
    new_config['Trakt']['trakt_use_recommended'] = int(TRAKT_USE_RECOMMENDED)
    new_config['Trakt']['trakt_sync'] = int(TRAKT_SYNC)
    new_config['Trakt']['trakt_sync_remove'] = int(TRAKT_SYNC_REMOVE)
    new_config['Trakt']['trakt_default_indexer'] = int(TRAKT_DEFAULT_INDEXER)
    new_config['Trakt']['trakt_timeout'] = int(TRAKT_TIMEOUT)
    new_config['Trakt']['trakt_blacklist_name'] = TRAKT_BLACKLIST_NAME

    new_config['pyTivo'] = {}
    new_config['pyTivo']['use_pytivo'] = int(USE_PYTIVO)
    new_config['pyTivo']['pytivo_notify_onsnatch'] = int(PYTIVO_NOTIFY_ONSNATCH)
    new_config['pyTivo']['pytivo_notify_ondownload'] = int(PYTIVO_NOTIFY_ONDOWNLOAD)
    new_config['pyTivo']['pytivo_notify_onsubtitledownload'] = int(PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['pyTivo']['pyTivo_update_library'] = int(PYTIVO_UPDATE_LIBRARY)
    new_config['pyTivo']['pytivo_host'] = PYTIVO_HOST
    new_config['pyTivo']['pytivo_share_name'] = PYTIVO_SHARE_NAME
    new_config['pyTivo']['pytivo_tivo_name'] = PYTIVO_TIVO_NAME

    new_config['NMA'] = {}
    new_config['NMA']['use_nma'] = int(USE_NMA)
    new_config['NMA']['nma_notify_onsnatch'] = int(NMA_NOTIFY_ONSNATCH)
    new_config['NMA']['nma_notify_ondownload'] = int(NMA_NOTIFY_ONDOWNLOAD)
    new_config['NMA']['nma_notify_onsubtitledownload'] = int(NMA_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['NMA']['nma_api'] = NMA_API
    new_config['NMA']['nma_priority'] = NMA_PRIORITY

    new_config['Pushalot'] = {}
    new_config['Pushalot']['use_pushalot'] = int(USE_PUSHALOT)
    new_config['Pushalot']['pushalot_notify_onsnatch'] = int(PUSHALOT_NOTIFY_ONSNATCH)
    new_config['Pushalot']['pushalot_notify_ondownload'] = int(PUSHALOT_NOTIFY_ONDOWNLOAD)
    new_config['Pushalot']['pushalot_notify_onsubtitledownload'] = int(PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Pushalot']['pushalot_authorizationtoken'] = PUSHALOT_AUTHORIZATIONTOKEN

    new_config['Pushbullet'] = {}
    new_config['Pushbullet']['use_pushbullet'] = int(USE_PUSHBULLET)
    new_config['Pushbullet']['pushbullet_notify_onsnatch'] = int(PUSHBULLET_NOTIFY_ONSNATCH)
    new_config['Pushbullet']['pushbullet_notify_ondownload'] = int(PUSHBULLET_NOTIFY_ONDOWNLOAD)
    new_config['Pushbullet']['pushbullet_notify_onsubtitledownload'] = int(PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Pushbullet']['pushbullet_api'] = PUSHBULLET_API
    new_config['Pushbullet']['pushbullet_device'] = PUSHBULLET_DEVICE

    new_config['Email'] = {}
    new_config['Email']['use_email'] = int(USE_EMAIL)
    new_config['Email']['email_notify_onsnatch'] = int(EMAIL_NOTIFY_ONSNATCH)
    new_config['Email']['email_notify_ondownload'] = int(EMAIL_NOTIFY_ONDOWNLOAD)
    new_config['Email']['email_notify_onsubtitledownload'] = int(EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD)
    new_config['Email']['email_host'] = EMAIL_HOST
    new_config['Email']['email_port'] = int(EMAIL_PORT)
    new_config['Email']['email_tls'] = int(EMAIL_TLS)
    new_config['Email']['email_user'] = EMAIL_USER
    new_config['Email']['email_password'] = helpers.encrypt(EMAIL_PASSWORD, ENCRYPTION_VERSION)
    new_config['Email']['email_from'] = EMAIL_FROM
    new_config['Email']['email_list'] = EMAIL_LIST

    new_config['Newznab'] = {}
    new_config['Newznab']['newznab_data'] = NEWZNAB_DATA

    new_config['TorrentRss'] = {}
    new_config['TorrentRss']['torrentrss_data'] = '!!!'.join([x.configStr() for x in torrentRssProviderList])

    new_config['GUI'] = {}
    new_config['GUI']['gui_name'] = GUI_NAME
    new_config['GUI']['theme_name'] = THEME_NAME
    new_config['GUI']['home_layout'] = HOME_LAYOUT
    new_config['GUI']['history_layout'] = HISTORY_LAYOUT
    new_config['GUI']['history_limit'] = HISTORY_LIMIT
    new_config['GUI']['display_show_specials'] = int(DISPLAY_SHOW_SPECIALS)
    new_config['GUI']['coming_eps_layout'] = COMING_EPS_LAYOUT
    new_config['GUI']['coming_eps_display_paused'] = int(COMING_EPS_DISPLAY_PAUSED)
    new_config['GUI']['coming_eps_sort'] = COMING_EPS_SORT
    new_config['GUI']['coming_eps_missed_range'] = int(COMING_EPS_MISSED_RANGE)
    new_config['GUI']['fuzzy_dating'] = int(FUZZY_DATING)
    new_config['GUI']['trim_zero'] = int(TRIM_ZERO)
    new_config['GUI']['date_preset'] = DATE_PRESET
    new_config['GUI']['time_preset'] = TIME_PRESET_W_SECONDS
    new_config['GUI']['timezone_display'] = TIMEZONE_DISPLAY
    new_config['GUI']['poster_sortby'] = POSTER_SORTBY
    new_config['GUI']['poster_sortdir'] = POSTER_SORTDIR
    new_config['GUI']['filter_row'] = int(FILTER_ROW)

    new_config['Subtitles'] = {}
    new_config['Subtitles']['use_subtitles'] = int(USE_SUBTITLES)
    new_config['Subtitles']['subtitles_languages'] = ','.join(SUBTITLES_LANGUAGES)
    new_config['Subtitles']['SUBTITLES_SERVICES_LIST'] = ','.join(SUBTITLES_SERVICES_LIST)
    new_config['Subtitles']['SUBTITLES_SERVICES_ENABLED'] = '|'.join([str(x) for x in SUBTITLES_SERVICES_ENABLED])
    new_config['Subtitles']['subtitles_dir'] = SUBTITLES_DIR
    new_config['Subtitles']['subtitles_default'] = int(SUBTITLES_DEFAULT)
    new_config['Subtitles']['subtitles_history'] = int(SUBTITLES_HISTORY)
    new_config['Subtitles']['embedded_subtitles_all'] = int(EMBEDDED_SUBTITLES_ALL)
    new_config['Subtitles']['subtitles_hearing_impaired'] = int(SUBTITLES_HEARING_IMPAIRED)
    new_config['Subtitles']['subtitles_finder_frequency'] = int(SUBTITLES_FINDER_FREQUENCY)
    new_config['Subtitles']['subtitles_multi'] = int(SUBTITLES_MULTI)
    new_config['Subtitles']['subtitles_extra_scripts'] = '|'.join(SUBTITLES_EXTRA_SCRIPTS)

    new_config['Subtitles']['addic7ed_username'] = ADDIC7ED_USER
    new_config['Subtitles']['addic7ed_password'] = helpers.encrypt(ADDIC7ED_PASS, ENCRYPTION_VERSION)

    new_config['Subtitles']['legendastv_username'] = LEGENDASTV_USER
    new_config['Subtitles']['legendastv_password'] = helpers.encrypt(LEGENDASTV_PASS, ENCRYPTION_VERSION)

    new_config['Subtitles']['opensubtitles_username'] = OPENSUBTITLES_USER
    new_config['Subtitles']['opensubtitles_password'] = helpers.encrypt(OPENSUBTITLES_PASS, ENCRYPTION_VERSION)

    new_config['FailedDownloads'] = {}
    new_config['FailedDownloads']['use_failed_downloads'] = int(USE_FAILED_DOWNLOADS)
    new_config['FailedDownloads']['delete_failed'] = int(DELETE_FAILED)

    new_config['ANIDB'] = {}
    new_config['ANIDB']['use_anidb'] = int(USE_ANIDB)
    new_config['ANIDB']['anidb_username'] = ANIDB_USERNAME
    new_config['ANIDB']['anidb_password'] = helpers.encrypt(ANIDB_PASSWORD, ENCRYPTION_VERSION)
    new_config['ANIDB']['anidb_use_mylist'] = int(ANIDB_USE_MYLIST)

    new_config['ANIME'] = {}
    new_config['ANIME']['anime_split_home'] = int(ANIME_SPLIT_HOME)

    new_config.write()


def launchBrowser(protocol='http', startPort=None, web_root='/'):
    if not startPort:
        startPort = WEB_PORT

    browserURL = '%s://localhost:%d%s/home/' % (protocol, startPort, web_root)

    try:
        webbrowser.open(browserURL, 2, 1)
    except Exception:
        try:
            webbrowser.open(browserURL, 1, 1)
        except Exception:
            logger.log(u"Unable to launch a browser", logger.ERROR)


def getEpList(epIDs, showid=None):
    if epIDs == None or len(epIDs) == 0:
        return []

    query = "SELECT * FROM tv_episodes WHERE indexerid in (%s)" % (",".join(['?'] * len(epIDs)),)
    params = epIDs

    if showid != None:
        query += " AND showid = ?"
        params.append(showid)

    myDB = db.DBConnection()
    sqlResults = myDB.select(query, params)

    epList = []

    for curEp in sqlResults:
        curShowObj = helpers.findCertainShow(showList, int(curEp["showid"]))
        curEpObj = curShowObj.getEpisode(int(curEp["season"]), int(curEp["episode"]))
        epList.append(curEpObj)

    return epList
