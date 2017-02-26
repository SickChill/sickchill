# coding=utf-8
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.
# pylint: disable=too-many-lines
import datetime
import gettext
import os
import random
import re
import shutil
import socket
import sys
from threading import Lock

import rarfile

try:
    import pytz  # pylint: disable=unused-import
except ImportError:
    pytz = None
    from pkg_resources import require
    require('pytz')


from sickbeard.indexers import indexer_api
from sickbeard.common import SD, SKIPPED, WANTED
from sickbeard.databases import mainDB, cache_db, failed_db
from sickbeard.providers.newznab import NewznabProvider
from sickbeard.providers.rsstorrent import TorrentRssProvider
from sickbeard.config import check_section, check_setting_int, check_setting_str, \
    check_setting_float, check_setting_bool, ConfigMigrator
from sickbeard import db, helpers, scheduler, search_queue, show_queue, logger, \
    naming, dailysearcher, metadata, providers
from sickbeard import searchBacklog, showUpdater, versionChecker, properFinder, \
    auto_postprocessor, post_processing_queue, subtitles, traktChecker
from sickbeard.indexers.indexer_exceptions import indexer_shownotfound, \
    indexer_showincomplete, indexer_exception, indexer_error, \
    indexer_episodenotfound, indexer_attributenotfound, indexer_seasonnotfound, \
    indexer_userabort

from sickrage.helper import setup_github
from sickrage.helper.encoding import ek
from sickrage.helper.exceptions import ex
from sickrage.providers.GenericProvider import GenericProvider
from sickrage.system.Shutdown import Shutdown

from configobj import ConfigObj

import requests

import six


gettext.install('messages', unicode=1, codeset='UTF-8')

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


requests.packages.urllib3.disable_warnings()
indexerApi = indexer_api.indexerApi

PID = None

CFG = None
CONFIG_FILE = None

# This is the version of the config we EXPECT to find
CONFIG_VERSION = 8

# Default encryption version (0 for None)
ENCRYPTION_VERSION = 0
ENCRYPTION_SECRET = None

PROG_DIR = '.'
MY_FULLNAME = None
LOCALE_DIR = 'locale'
MY_NAME = None
MY_ARGS = []
SYS_ENCODING = ''
DATA_DIR = ''
CREATEPID = False
PIDFILE = ''

SITE_MESSAGES = {}

DAEMON = None
NO_RESIZE = False

# system events
events = None

# github
gh = None

# schedulers
dailySearchScheduler = None
backlogSearchScheduler = None
showUpdateScheduler = None
versionCheckScheduler = None
showQueueScheduler = None
searchQueueScheduler = None
properFinderScheduler = None
autoPostProcessorScheduler = None
postProcessorTaskScheduler = None
subtitlesFinderScheduler = None
traktCheckerScheduler = None

showList = []

providerList = []
newznabProviderList = []
torrentRssProviderList = []
metadata_provider_dict = {}

VERSION_NOTIFY = False
AUTO_UPDATE = False
NOTIFY_ON_UPDATE = False
CUR_COMMIT_HASH = None
BRANCH = ''

GIT_RESET = True
GIT_REMOTE = ''
GIT_REMOTE_URL = ''
CUR_COMMIT_BRANCH = ''
GIT_ORG = 'SickRage'
GIT_REPO = 'SickRage'
GIT_AUTH_TYPE = 0
GIT_USERNAME = None
GIT_PASSWORD = None
GIT_TOKEN = None
GIT_PATH = None
DEVELOPER = False

NEWS_URL = 'http://sickrage.github.io/sickrage-news/news.md'
LOGO_URL = 'http://sickrage.github.io/images/ico/favicon-64.png'

NEWS_LAST_READ = None
NEWS_LATEST = None
NEWS_UNREAD = 0

INIT_LOCK = Lock()
started = {}

ACTUAL_LOG_DIR = None
LOG_DIR = None
LOG_NR = 5
LOG_SIZE = 10.0

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
PROXY_INDEXERS = False
SSL_VERIFY = True

LOCALHOST_IP = None

CPU_PRESET = None

ANON_REDIRECT = None

API_KEY = None
API_ROOT = None

ENABLE_HTTPS = False
NOTIFY_ON_LOGIN = False
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
DBDEBUG = False
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
SEASON_FOLDERS_DEFAULT = False
SUBTITLES_DEFAULT = False
INDEXER_DEFAULT = None
INDEXER_TIMEOUT = None
SCENE_DEFAULT = False
ANIME_DEFAULT = False
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

AUTOPOSTPROCESSOR_FREQUENCY = None
DAILYSEARCH_FREQUENCY = None
UPDATE_FREQUENCY = None
BACKLOG_FREQUENCY = None
SHOWUPDATE_HOUR = None

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

ADD_SHOWS_WO_DIR = False
CREATE_MISSING_SHOW_DIRS = False
RENAME_EPISODES = False
AIRDATE_EPISODES = False
FILE_TIMESTAMP_TIMEZONE = None
PROCESS_AUTOMATICALLY = False
NO_DELETE = False
USE_ICACLS = True
KEEP_PROCESSED_DIR = False
PROCESS_METHOD = None
DELRARCONTENTS = False
MOVE_ASSOCIATED_FILES = False
DELETE_NON_ASSOCIATED_FILES = False
POSTPONE_IF_SYNC_FILES = True
NFO_RENAME = True
TV_DOWNLOAD_DIR = None
UNPACK = False
UNPACK_DIR = ''
UNRAR_TOOL = rarfile.UNRAR_TOOL
ALT_UNRAR_TOOL = rarfile.ALT_TOOL

SKIP_REMOVED_FILES = False
ALLOWED_EXTENSIONS = "srt,nfo,srr,sfv"
USE_FREE_SPACE_CHECK = True

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

SYNOLOGY_DSM_HOST = None
SYNOLOGY_DSM_USERNAME = None
SYNOLOGY_DSM_PASSWORD = None
SYNOLOGY_DSM_PATH = None

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

USE_PLEX_SERVER = False
PLEX_NOTIFY_ONSNATCH = False
PLEX_NOTIFY_ONDOWNLOAD = False
PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = False
PLEX_UPDATE_LIBRARY = False
PLEX_SERVER_HOST = None
PLEX_SERVER_TOKEN = None
PLEX_CLIENT_HOST = None
PLEX_SERVER_USERNAME = None
PLEX_SERVER_PASSWORD = None

USE_PLEX_CLIENT = False
PLEX_CLIENT_USERNAME = None
PLEX_CLIENT_PASSWORD = None
PLEX_SERVER_HTTPS = None

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

USE_TELEGRAM = False
TELEGRAM_NOTIFY_ONSNATCH = False
TELEGRAM_NOTIFY_ONDOWNLOAD = False
TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = False
TELEGRAM_ID = ''
TELEGRAM_APIKEY = ''

USE_JOIN = False
JOIN_NOTIFY_ONSNATCH = False
JOIN_NOTIFY_ONDOWNLOAD = False
JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = False
JOIN_ID = ''

USE_PROWL = False
PROWL_NOTIFY_ONSNATCH = False
PROWL_NOTIFY_ONDOWNLOAD = False
PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = False
PROWL_API = None
PROWL_PRIORITY = 0
PROWL_MESSAGE_TITLE = 'SickRage'

USE_TWITTER = False
TWITTER_NOTIFY_ONSNATCH = False
TWITTER_NOTIFY_ONDOWNLOAD = False
TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = False
TWITTER_USERNAME = None
TWITTER_PASSWORD = None
TWITTER_PREFIX = None
TWITTER_DMTO = None
TWITTER_USEDM = False

USE_TWILIO = False
TWILIO_NOTIFY_ONSNATCH = False
TWILIO_NOTIFY_ONDOWNLOAD = False
TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = False
TWILIO_PHONE_SID = ''
TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_TO_NUMBER = ''

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
PUSHOVER_PRIORITY = 0

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

USE_SLACK = False
SLACK_NOTIFY_SNATCH = None
SLACK_NOTIFY_DOWNLOAD = None
SLACK_NOTIFY_SUBTITLEDOWNLOAD = None
SLACK_WEBHOOK = None

USE_DISCORD = False
DISCORD_NOTIFY_SNATCH = None
DISCORD_NOTIFY_DOWNLOAD = None
DISCORD_NOTIFY_SUBTITLEDOWNLOAD = None
DISCORD_WEBHOOK = None
DISCORD_NAME = 'SickRage'
DISCORD_AVATAR_URL = 'https://raw.githubusercontent.com/SickRage/SickRage/master/gui/slick/images/sickrage-shark-mascot.png'
DISCORD_TTS = False

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
PUSHBULLET_CHANNEL = None

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
EMAIL_SUBJECT = None

GUI_NAME = None
GUI_LANG = None

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
SICKRAGE_BACKGROUND = None
SICKRAGE_BACKGROUND_PATH = None
FANART_BACKGROUND = None
FANART_BACKGROUND_OPACITY = None

USE_SUBTITLES = False
SUBTITLES_LANGUAGES = []
SUBTITLES_DIR = ''
SUBTITLES_SERVICES_LIST = []
SUBTITLES_SERVICES_ENABLED = []
SUBTITLES_HISTORY = False
SUBTITLES_PERFECT_MATCH = False
EMBEDDED_SUBTITLES_ALL = False
SUBTITLES_HEARING_IMPAIRED = False
SUBTITLES_FINDER_FREQUENCY = 1
SUBTITLES_MULTI = False
SUBTITLES_EXTRA_SCRIPTS = []
SUBTITLES_KEEP_ONLY_WANTED = False

ADDIC7ED_USER = ADDIC7ED_PASS = None
OPENSUBTITLES_USER = OPENSUBTITLES_PASS = None
LEGENDASTV_USER = LEGENDASTV_PASS = None
ITASA_USER = ITASA_PASS = None

USE_FAILED_DOWNLOADS = False
DELETE_FAILED = False

EXTRA_SCRIPTS = []

IGNORE_WORDS = "german,french,core2hd,dutch,swedish,reenc,MrLss"

TRACKERS_LIST = "udp://coppersurfer.tk:6969/announce,udp://open.demonii.com:1337,"
TRACKERS_LIST += "udp://exodus.desync.com:6969,udp://9.rarbg.me:2710/announce,"
TRACKERS_LIST += "udp://glotorrents.pw:6969/announce,udp://tracker.openbittorrent.com:80/announce,"
TRACKERS_LIST += "udp://9.rarbg.to:2710/announce"

REQUIRE_WORDS = ""
IGNORED_SUBS_LIST = "dk,fin,heb,kor,nor,nordic,pl,swe"
SYNC_FILES = "!sync,lftp-pget-status,bts,!qb,!qB"

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

__INITIALIZED__ = {}

NEWZNAB_DATA = None


def get_backlog_cycle_time():
    cycletime = DAILYSEARCH_FREQUENCY * 2 + 7
    return max([cycletime, 720])


def initialize(consoleLogging=True):  # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    with INIT_LOCK:
        # pylint: disable=global-statement
        global BRANCH, GIT_RESET, GIT_REMOTE, GIT_REMOTE_URL, CUR_COMMIT_HASH, CUR_COMMIT_BRANCH, ACTUAL_LOG_DIR, LOG_DIR, LOG_NR, LOG_SIZE, WEB_PORT, WEB_LOG, ENCRYPTION_VERSION, ENCRYPTION_SECRET, WEB_ROOT, WEB_USERNAME, WEB_PASSWORD, WEB_HOST, WEB_IPV6, WEB_COOKIE_SECRET, WEB_USE_GZIP, API_KEY, ENABLE_HTTPS, HTTPS_CERT, HTTPS_KEY, \
            HANDLE_REVERSE_PROXY, USE_NZBS, USE_TORRENTS, NZB_METHOD, NZB_DIR, DOWNLOAD_PROPERS, RANDOMIZE_PROVIDERS, CHECK_PROPERS_INTERVAL, ALLOW_HIGH_PRIORITY, SAB_FORCED, TORRENT_METHOD, NOTIFY_ON_LOGIN, \
            SAB_USERNAME, SAB_PASSWORD, SAB_APIKEY, SAB_CATEGORY, SAB_CATEGORY_BACKLOG, SAB_CATEGORY_ANIME, SAB_CATEGORY_ANIME_BACKLOG, SAB_HOST, \
            NZBGET_USERNAME, NZBGET_PASSWORD, NZBGET_CATEGORY, NZBGET_CATEGORY_BACKLOG, NZBGET_CATEGORY_ANIME, NZBGET_CATEGORY_ANIME_BACKLOG, NZBGET_PRIORITY, NZBGET_HOST, NZBGET_USE_HTTPS, backlogSearchScheduler, \
            TORRENT_USERNAME, TORRENT_PASSWORD, TORRENT_HOST, TORRENT_PATH, TORRENT_SEED_TIME, TORRENT_PAUSED, TORRENT_HIGH_BANDWIDTH, TORRENT_LABEL, TORRENT_LABEL_ANIME, TORRENT_VERIFY_CERT, TORRENT_RPCURL, TORRENT_AUTH_TYPE, \
            USE_KODI, KODI_ALWAYS_ON, KODI_NOTIFY_ONSNATCH, KODI_NOTIFY_ONDOWNLOAD, KODI_NOTIFY_ONSUBTITLEDOWNLOAD, KODI_UPDATE_FULL, KODI_UPDATE_ONLYFIRST, \
            KODI_UPDATE_LIBRARY, KODI_HOST, KODI_USERNAME, KODI_PASSWORD, BACKLOG_FREQUENCY, \
            USE_TRAKT, TRAKT_USERNAME, TRAKT_ACCESS_TOKEN, TRAKT_REFRESH_TOKEN, TRAKT_REMOVE_WATCHLIST, TRAKT_SYNC_WATCHLIST, TRAKT_REMOVE_SHOW_FROM_SICKRAGE, TRAKT_METHOD_ADD, TRAKT_START_PAUSED, traktCheckerScheduler, TRAKT_USE_RECOMMENDED, TRAKT_SYNC, TRAKT_SYNC_REMOVE, TRAKT_DEFAULT_INDEXER, TRAKT_REMOVE_SERIESLIST, TRAKT_TIMEOUT, TRAKT_BLACKLIST_NAME, \
            USE_PLEX_SERVER, PLEX_NOTIFY_ONSNATCH, PLEX_NOTIFY_ONDOWNLOAD, PLEX_NOTIFY_ONSUBTITLEDOWNLOAD, PLEX_UPDATE_LIBRARY, USE_PLEX_CLIENT, PLEX_CLIENT_USERNAME, PLEX_CLIENT_PASSWORD, \
            PLEX_SERVER_HOST, PLEX_SERVER_TOKEN, PLEX_CLIENT_HOST, PLEX_SERVER_USERNAME, PLEX_SERVER_PASSWORD, PLEX_SERVER_HTTPS, MIN_BACKLOG_FREQUENCY, SKIP_REMOVED_FILES, ALLOWED_EXTENSIONS, \
            USE_EMBY, EMBY_HOST, EMBY_APIKEY, SITE_MESSAGES, \
            showUpdateScheduler, INDEXER_DEFAULT_LANGUAGE, EP_DEFAULT_DELETED_STATUS, LAUNCH_BROWSER, TRASH_REMOVE_SHOW, TRASH_ROTATE_LOGS, SORT_ARTICLE, \
            NEWZNAB_DATA, NZBS, NZBS_UID, NZBS_HASH, INDEXER_DEFAULT, INDEXER_TIMEOUT, USENET_RETENTION, TORRENT_DIR, \
            QUALITY_DEFAULT, SEASON_FOLDERS_DEFAULT, SUBTITLES_DEFAULT, STATUS_DEFAULT, STATUS_DEFAULT_AFTER, \
            GROWL_NOTIFY_ONSNATCH, GROWL_NOTIFY_ONDOWNLOAD, GROWL_NOTIFY_ONSUBTITLEDOWNLOAD, TWITTER_NOTIFY_ONSNATCH, TWITTER_NOTIFY_ONDOWNLOAD, TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD, USE_FREEMOBILE, FREEMOBILE_ID, FREEMOBILE_APIKEY, FREEMOBILE_NOTIFY_ONSNATCH, FREEMOBILE_NOTIFY_ONDOWNLOAD, FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_TELEGRAM, TELEGRAM_ID, TELEGRAM_APIKEY, TELEGRAM_NOTIFY_ONSNATCH, TELEGRAM_NOTIFY_ONDOWNLOAD, TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_JOIN, JOIN_ID, JOIN_NOTIFY_ONSNATCH, JOIN_NOTIFY_ONDOWNLOAD, JOIN_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_GROWL, GROWL_HOST, GROWL_PASSWORD, USE_PROWL, PROWL_NOTIFY_ONSNATCH, PROWL_NOTIFY_ONDOWNLOAD, PROWL_NOTIFY_ONSUBTITLEDOWNLOAD, PROWL_API, PROWL_PRIORITY, PROWL_MESSAGE_TITLE, \
            USE_PYTIVO, PYTIVO_NOTIFY_ONSNATCH, PYTIVO_NOTIFY_ONDOWNLOAD, PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD, PYTIVO_UPDATE_LIBRARY, PYTIVO_HOST, PYTIVO_SHARE_NAME, PYTIVO_TIVO_NAME, \
            USE_NMA, NMA_NOTIFY_ONSNATCH, NMA_NOTIFY_ONDOWNLOAD, NMA_NOTIFY_ONSUBTITLEDOWNLOAD, NMA_API, NMA_PRIORITY, \
            USE_PUSHALOT, PUSHALOT_NOTIFY_ONSNATCH, PUSHALOT_NOTIFY_ONDOWNLOAD, PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHALOT_AUTHORIZATIONTOKEN, \
            USE_PUSHBULLET, PUSHBULLET_NOTIFY_ONSNATCH, PUSHBULLET_NOTIFY_ONDOWNLOAD, PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHBULLET_API, PUSHBULLET_DEVICE, PUSHBULLET_CHANNEL,\
            versionCheckScheduler, VERSION_NOTIFY, AUTO_UPDATE, NOTIFY_ON_UPDATE, PROCESS_AUTOMATICALLY, NO_DELETE, USE_ICACLS, UNPACK, CPU_PRESET, \
            UNPACK_DIR, UNRAR_TOOL, ALT_UNRAR_TOOL, KEEP_PROCESSED_DIR, PROCESS_METHOD, DELRARCONTENTS, TV_DOWNLOAD_DIR, UPDATE_FREQUENCY, \
            showQueueScheduler, searchQueueScheduler, postProcessorTaskScheduler, ROOT_DIRS, CACHE_DIR, ACTUAL_CACHE_DIR, TIMEZONE_DISPLAY, \
            NAMING_PATTERN, NAMING_MULTI_EP, NAMING_ANIME_MULTI_EP, NAMING_FORCE_FOLDERS, NAMING_ABD_PATTERN, NAMING_CUSTOM_ABD, NAMING_SPORTS_PATTERN, NAMING_CUSTOM_SPORTS, NAMING_ANIME_PATTERN, NAMING_CUSTOM_ANIME, NAMING_STRIP_YEAR, \
            RENAME_EPISODES, AIRDATE_EPISODES, FILE_TIMESTAMP_TIMEZONE, properFinderScheduler, PROVIDER_ORDER, autoPostProcessorScheduler, \
            providerList, newznabProviderList, torrentRssProviderList, \
            EXTRA_SCRIPTS, USE_TWITTER, TWITTER_USERNAME, TWITTER_PASSWORD, TWITTER_PREFIX, DAILYSEARCH_FREQUENCY, TWITTER_DMTO, TWITTER_USEDM, \
            USE_TWILIO, TWILIO_NOTIFY_ONSNATCH, TWILIO_NOTIFY_ONDOWNLOAD, TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD, TWILIO_PHONE_SID, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_TO_NUMBER, \
            USE_BOXCAR2, BOXCAR2_ACCESSTOKEN, BOXCAR2_NOTIFY_ONDOWNLOAD, BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD, BOXCAR2_NOTIFY_ONSNATCH, \
            USE_PUSHOVER, PUSHOVER_USERKEY, PUSHOVER_APIKEY, PUSHOVER_DEVICE, PUSHOVER_NOTIFY_ONDOWNLOAD, PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD, PUSHOVER_NOTIFY_ONSNATCH, PUSHOVER_SOUND, PUSHOVER_PRIORITY, \
            USE_LIBNOTIFY, LIBNOTIFY_NOTIFY_ONSNATCH, LIBNOTIFY_NOTIFY_ONDOWNLOAD, LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD, USE_NMJ, NMJ_HOST, NMJ_DATABASE, NMJ_MOUNT, USE_NMJv2, NMJv2_HOST, NMJv2_DATABASE, NMJv2_DBLOC, USE_SYNOINDEX, \
            USE_SYNOLOGYNOTIFIER, SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH, SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD, SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD, \
            USE_EMAIL, EMAIL_HOST, EMAIL_PORT, EMAIL_TLS, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM, EMAIL_NOTIFY_ONSNATCH, EMAIL_NOTIFY_ONDOWNLOAD, EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD, EMAIL_LIST, EMAIL_SUBJECT, \
            USE_LISTVIEW, METADATA_KODI, METADATA_KODI_12PLUS, METADATA_MEDIABROWSER, METADATA_PS3, metadata_provider_dict, \
            NEWZBIN, NEWZBIN_USERNAME, NEWZBIN_PASSWORD, GIT_PATH, MOVE_ASSOCIATED_FILES, DELETE_NON_ASSOCIATED_FILES, SYNC_FILES, POSTPONE_IF_SYNC_FILES, dailySearchScheduler, NFO_RENAME, \
            GUI_NAME, HOME_LAYOUT, HISTORY_LAYOUT, DISPLAY_SHOW_SPECIALS, COMING_EPS_LAYOUT, COMING_EPS_SORT, COMING_EPS_DISPLAY_PAUSED, COMING_EPS_MISSED_RANGE, FUZZY_DATING, TRIM_ZERO, DATE_PRESET, TIME_PRESET, TIME_PRESET_W_SECONDS, THEME_NAME, \
            POSTER_SORTBY, POSTER_SORTDIR, HISTORY_LIMIT, CREATE_MISSING_SHOW_DIRS, ADD_SHOWS_WO_DIR, USE_FREE_SPACE_CHECK, \
            METADATA_WDTV, METADATA_TIVO, METADATA_MEDE8ER, IGNORE_WORDS, TRACKERS_LIST, IGNORED_SUBS_LIST, REQUIRE_WORDS, CALENDAR_UNPROTECTED, CALENDAR_ICONS, NO_RESTART, \
            USE_SUBTITLES, SUBTITLES_LANGUAGES, SUBTITLES_DIR, SUBTITLES_SERVICES_LIST, SUBTITLES_SERVICES_ENABLED, SUBTITLES_HISTORY, SUBTITLES_FINDER_FREQUENCY, SUBTITLES_MULTI, SUBTITLES_KEEP_ONLY_WANTED, EMBEDDED_SUBTITLES_ALL, SUBTITLES_EXTRA_SCRIPTS, SUBTITLES_PERFECT_MATCH, subtitlesFinderScheduler, \
            SUBTITLES_HEARING_IMPAIRED, ADDIC7ED_USER, ADDIC7ED_PASS, ITASA_USER, ITASA_PASS, LEGENDASTV_USER, LEGENDASTV_PASS, OPENSUBTITLES_USER, OPENSUBTITLES_PASS, \
            USE_FAILED_DOWNLOADS, DELETE_FAILED, ANON_REDIRECT, LOCALHOST_IP, DEBUG, DBDEBUG, DEFAULT_PAGE, PROXY_SETTING, PROXY_INDEXERS, \
            AUTOPOSTPROCESSOR_FREQUENCY, SHOWUPDATE_HOUR, \
            ANIME_DEFAULT, NAMING_ANIME, ANIMESUPPORT, USE_ANIDB, ANIDB_USERNAME, ANIDB_PASSWORD, ANIDB_USE_MYLIST, \
            ANIME_SPLIT_HOME, SCENE_DEFAULT, DOWNLOAD_URL, BACKLOG_DAYS, GIT_AUTH_TYPE, GIT_USERNAME, GIT_PASSWORD, GIT_TOKEN, \
            DEVELOPER, DISPLAY_ALL_SEASONS, SSL_VERIFY, NEWS_LAST_READ, NEWS_LATEST, SOCKET_TIMEOUT, \
            SYNOLOGY_DSM_HOST, SYNOLOGY_DSM_USERNAME, SYNOLOGY_DSM_PASSWORD, SYNOLOGY_DSM_PATH, GUI_LANG, SICKRAGE_BACKGROUND, SICKRAGE_BACKGROUND_PATH, \
            FANART_BACKGROUND, FANART_BACKGROUND_OPACITY, USE_SLACK, SLACK_NOTIFY_SNATCH, SLACK_NOTIFY_DOWNLOAD, SLACK_WEBHOOK, \
            USE_DISCORD, DISCORD_NOTIFY_SNATCH, DISCORD_NOTIFY_DOWNLOAD, DISCORD_WEBHOOK

        if __INITIALIZED__:
            return False

        check_section(CFG, 'General')
        check_section(CFG, 'Blackhole')
        check_section(CFG, 'Newzbin')
        check_section(CFG, 'SABnzbd')
        check_section(CFG, 'NZBget')
        check_section(CFG, 'KODI')
        check_section(CFG, 'PLEX')
        check_section(CFG, 'Emby')
        check_section(CFG, 'Growl')
        check_section(CFG, 'Prowl')
        check_section(CFG, 'Twitter')
        check_section(CFG, 'Boxcar2')
        check_section(CFG, 'NMJ')
        check_section(CFG, 'NMJv2')
        check_section(CFG, 'Synology')
        check_section(CFG, 'SynologyNotifier')
        check_section(CFG, 'pyTivo')
        check_section(CFG, 'NMA')
        check_section(CFG, 'Pushalot')
        check_section(CFG, 'Pushbullet')
        check_section(CFG, 'Subtitles')
        check_section(CFG, 'pyTivo')
        check_section(CFG, 'Slack')
        check_section(CFG, 'Discord')

        # Need to be before any passwords
        ENCRYPTION_VERSION = check_setting_int(CFG, 'General', 'encryption_version')
        ENCRYPTION_SECRET = check_setting_str(CFG, 'General', 'encryption_secret', helpers.generateCookieSecret(), censor_log=True)

        # git login info
        GIT_AUTH_TYPE = check_setting_int(CFG, 'General', 'git_auth_type')
        GIT_USERNAME = check_setting_str(CFG, 'General', 'git_username')
        GIT_PASSWORD = check_setting_str(CFG, 'General', 'git_password', censor_log=True)
        GIT_TOKEN = check_setting_str(CFG, 'General', 'git_token_password', censor_log=True) # encryption needed
        DEVELOPER = check_setting_bool(CFG, 'General', 'developer')

        # debugging
        DEBUG = check_setting_bool(CFG, 'General', 'debug')
        DBDEBUG = check_setting_bool(CFG, 'General', 'dbdebug')

        DEFAULT_PAGE = check_setting_str(CFG, 'General', 'default_page', 'home')
        if DEFAULT_PAGE not in ('home', 'schedule', 'history', 'news', 'IRC'):
            DEFAULT_PAGE = 'home'

        ACTUAL_LOG_DIR = check_setting_str(CFG, 'General', 'log_dir', 'Logs')
        LOG_DIR = ek(os.path.normpath, ek(os.path.join, DATA_DIR, ACTUAL_LOG_DIR))
        LOG_NR = check_setting_int(CFG, 'General', 'log_nr', 5)  # Default to 5 backup file (sickrage.log.x)
        LOG_SIZE = check_setting_float(CFG, 'General', 'log_size', 10.0)  # Default to max 10MB per logfile

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

        if 'sickragetv' in GIT_REMOTE_URL.lower():
            GIT_REMOTE_URL = 'https://github.com/SickRage/SickRage.git'

        # current commit hash
        CUR_COMMIT_HASH = check_setting_str(CFG, 'General', 'cur_commit_hash')

        # current commit branch
        CUR_COMMIT_BRANCH = check_setting_str(CFG, 'General', 'cur_commit_branch')

        ACTUAL_CACHE_DIR = check_setting_str(CFG, 'General', 'cache_dir', 'cache')

        # fix bad configs due to buggy code
        if ACTUAL_CACHE_DIR == 'None':
            ACTUAL_CACHE_DIR = 'cache'

        # unless they specify, put the cache dir inside the data dir
        if not ek(os.path.isabs, ACTUAL_CACHE_DIR):
            CACHE_DIR = ek(os.path.join, DATA_DIR, ACTUAL_CACHE_DIR)
        else:
            CACHE_DIR = ACTUAL_CACHE_DIR

        if not helpers.makeDir(CACHE_DIR):
            logger.log(u"!!! Creating local cache dir failed, using system default", logger.ERROR)
            CACHE_DIR = None

        # Check if we need to perform a restore of the cache folder
        try:
            restoreDir = ek(os.path.join, DATA_DIR, 'restore')
            if ek(os.path.exists, restoreDir) and ek(os.path.exists, ek(os.path.join, restoreDir, 'cache')):
                def restoreCache(srcDir, dstDir):
                    def path_leaf(path):
                        head, tail = ek(os.path.split, path)
                        return tail or ek(os.path.basename, head)

                    try:
                        if ek(os.path.isdir, dstDir):
                            bakFilename = '{0}-{1}'.format(path_leaf(dstDir), datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S'))
                            shutil.move(dstDir, ek(os.path.join, ek(os.path.dirname, dstDir), bakFilename))

                        shutil.move(srcDir, dstDir)
                        logger.log(u"Restore: restoring cache successful", logger.INFO)
                    except Exception as e:
                        logger.log(u"Restore: restoring cache failed: {0}".format(e), logger.ERROR)

                restoreCache(ek(os.path.join, restoreDir, 'cache'), CACHE_DIR)
        except Exception as e:
            logger.log(u"Restore: restoring cache failed: {0}".format(ex(e)), logger.ERROR)
        finally:
            if ek(os.path.exists, ek(os.path.join, DATA_DIR, 'restore')):
                try:
                    shutil.rmtree(ek(os.path.join, DATA_DIR, 'restore'))
                except Exception as e:
                    logger.log(u"Restore: Unable to remove the restore directory: {0}".format(ex(e)), logger.ERROR)

                for cleanupDir in ['mako', 'sessions', 'indexers', 'rss']:
                    try:
                        shutil.rmtree(ek(os.path.join, CACHE_DIR, cleanupDir))
                    except Exception as e:
                        if cleanupDir not in ['rss', 'sessions', 'indexers']:
                            logger.log(u"Restore: Unable to remove the cache/{0} directory: {1}".format(cleanupDir, ex(e)), logger.WARNING)

        THEME_NAME = check_setting_str(CFG, 'GUI', 'theme_name', 'dark')
        SICKRAGE_BACKGROUND = check_setting_bool(CFG, 'GUI', 'sickrage_background')
        SICKRAGE_BACKGROUND_PATH = check_setting_str(CFG, 'GUI', 'sickrage_background_path')
        FANART_BACKGROUND = check_setting_bool(CFG, 'GUI', 'fanart_background', True)
        FANART_BACKGROUND_OPACITY = check_setting_float(CFG, 'GUI', 'fanart_background_opacity', 0.4)

        GUI_NAME = check_setting_str(CFG, 'GUI', 'gui_name', 'slick')
        GUI_LANG = check_setting_str(CFG, 'GUI', 'language')
        if GUI_LANG:
            gettext.translation('messages', LOCALE_DIR, languages=[GUI_LANG], codeset='UTF-8').install(unicode=1)
        else:
            gettext.install('messages', LOCALE_DIR, unicode=1, codeset='UTF-8')

        SOCKET_TIMEOUT = check_setting_int(CFG, 'General', 'socket_timeout', 30)
        socket.setdefaulttimeout(SOCKET_TIMEOUT)

        try:
            WEB_PORT = check_setting_int(CFG, 'General', 'web_port', 8081)
        except Exception:
            WEB_PORT = 8081

        if 21 > WEB_PORT > 65535:
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

        WEB_USE_GZIP = check_setting_bool(CFG, 'General', 'web_use_gzip', True)

        SSL_VERIFY = check_setting_bool(CFG, 'General', 'ssl_verify', True)

        INDEXER_DEFAULT_LANGUAGE = check_setting_str(CFG, 'General', 'indexerDefaultLang', 'en')
        EP_DEFAULT_DELETED_STATUS = check_setting_int(CFG, 'General', 'ep_default_deleted_status', 6)

        LAUNCH_BROWSER = check_setting_bool(CFG, 'General', 'launch_browser', True)

        DOWNLOAD_URL = check_setting_str(CFG, 'General', 'download_url')

        LOCALHOST_IP = check_setting_str(CFG, 'General', 'localhost_ip')

        CPU_PRESET = check_setting_str(CFG, 'General', 'cpu_preset', 'NORMAL')

        ANON_REDIRECT = check_setting_str(CFG, 'General', 'anon_redirect', 'http://dereferer.org/?')
        PROXY_SETTING = check_setting_str(CFG, 'General', 'proxy_setting')
        PROXY_INDEXERS = check_setting_int(CFG, 'General', 'proxy_indexers', 1)

        # attempt to help prevent users from breaking links by using a bad url
        if not ANON_REDIRECT.endswith('?'):
            ANON_REDIRECT = ''

        TRASH_REMOVE_SHOW = check_setting_bool(CFG, 'General', 'trash_remove_show')
        TRASH_ROTATE_LOGS = check_setting_bool(CFG, 'General', 'trash_rotate_logs')

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
        STATUS_DEFAULT = check_setting_int(CFG, 'General', 'status_default', SKIPPED)
        STATUS_DEFAULT_AFTER = check_setting_int(CFG, 'General', 'status_default_after', WANTED)
        VERSION_NOTIFY = check_setting_bool(CFG, 'General', 'version_notify', True)
        AUTO_UPDATE = check_setting_bool(CFG, 'General', 'auto_update')
        NOTIFY_ON_UPDATE = check_setting_bool(CFG, 'General', 'notify_on_update', True)
        SEASON_FOLDERS_DEFAULT = check_setting_bool(CFG, 'General', 'season_folders_default', True)
        INDEXER_DEFAULT = check_setting_int(CFG, 'General', 'indexer_default')
        INDEXER_TIMEOUT = check_setting_int(CFG, 'General', 'indexer_timeout', 20)
        ANIME_DEFAULT = check_setting_bool(CFG, 'General', 'anime_default')
        SCENE_DEFAULT = check_setting_bool(CFG, 'General', 'scene_default')

        PROVIDER_ORDER = check_setting_str(CFG, 'General', 'provider_order').split()

        NAMING_PATTERN = check_setting_str(CFG, 'General', 'naming_pattern', 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ABD_PATTERN = check_setting_str(CFG, 'General', 'naming_abd_pattern', '%SN - %A.D - %EN')
        NAMING_CUSTOM_ABD = check_setting_bool(CFG, 'General', 'naming_custom_abd')
        NAMING_SPORTS_PATTERN = check_setting_str(CFG, 'General', 'naming_sports_pattern', '%SN - %A-D - %EN')
        NAMING_ANIME_PATTERN = check_setting_str(CFG, 'General', 'naming_anime_pattern',
                                                 'Season %0S/%SN - S%0SE%0E - %EN')
        NAMING_ANIME = check_setting_int(CFG, 'General', 'naming_anime', 3)
        NAMING_CUSTOM_SPORTS = check_setting_bool(CFG, 'General', 'naming_custom_sports')
        NAMING_CUSTOM_ANIME = check_setting_bool(CFG, 'General', 'naming_custom_anime')
        NAMING_MULTI_EP = check_setting_int(CFG, 'General', 'naming_multi_ep', 1)
        NAMING_ANIME_MULTI_EP = check_setting_int(CFG, 'General', 'naming_anime_multi_ep', 1)
        NAMING_FORCE_FOLDERS = naming.check_force_season_folders()
        NAMING_STRIP_YEAR = check_setting_bool(CFG, 'General', 'naming_strip_year')

        USE_NZBS = check_setting_bool(CFG, 'General', 'use_nzbs')
        USE_TORRENTS = check_setting_bool(CFG, 'General', 'use_torrents', True)

        NZB_METHOD = check_setting_str(CFG, 'General', 'nzb_method', 'blackhole')
        if NZB_METHOD not in ('blackhole', 'sabnzbd', 'nzbget', 'download_station'):
            NZB_METHOD = 'blackhole'

        TORRENT_METHOD = check_setting_str(CFG, 'General', 'torrent_method', 'blackhole')
        if TORRENT_METHOD not in ('blackhole', 'utorrent', 'transmission', 'deluge', 'deluged', 'download_station', 'rtorrent', 'qbittorrent', 'mlnet', 'putio'):
            TORRENT_METHOD = 'blackhole'

        DOWNLOAD_PROPERS = check_setting_bool(CFG, 'General', 'download_propers', True)
        CHECK_PROPERS_INTERVAL = check_setting_str(CFG, 'General', 'check_propers_interval')
        if CHECK_PROPERS_INTERVAL not in ('15m', '45m', '90m', '4h', 'daily'):
            CHECK_PROPERS_INTERVAL = 'daily'

        RANDOMIZE_PROVIDERS = check_setting_bool(CFG, 'General', 'randomize_providers')

        ALLOW_HIGH_PRIORITY = check_setting_bool(CFG, 'General', 'allow_high_priority', True)

        SKIP_REMOVED_FILES = check_setting_bool(CFG, 'General', 'skip_removed_files')

        ALLOWED_EXTENSIONS = check_setting_str(CFG, 'General', 'allowed_extensions', ALLOWED_EXTENSIONS)

        USENET_RETENTION = check_setting_int(CFG, 'General', 'usenet_retention', 500)

        AUTOPOSTPROCESSOR_FREQUENCY = check_setting_int(CFG, 'General', 'autopostprocessor_frequency',
                                                        DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY)
        if AUTOPOSTPROCESSOR_FREQUENCY < MIN_AUTOPOSTPROCESSOR_FREQUENCY:
            AUTOPOSTPROCESSOR_FREQUENCY = MIN_AUTOPOSTPROCESSOR_FREQUENCY

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

        NZB_DIR = check_setting_str(CFG, 'Blackhole', 'nzb_dir')
        TORRENT_DIR = check_setting_str(CFG, 'Blackhole', 'torrent_dir')

        TV_DOWNLOAD_DIR = check_setting_str(CFG, 'General', 'tv_download_dir')
        PROCESS_AUTOMATICALLY = check_setting_bool(CFG, 'General', 'process_automatically')
        NO_DELETE = check_setting_bool(CFG, 'General', 'no_delete')
        USE_ICACLS = check_setting_bool(CFG, 'General', 'use_icacls', True)
        UNPACK = check_setting_bool(CFG, 'General', 'unpack')
        UNPACK_DIR = check_setting_str(CFG, 'General', 'unpack_dir')
        UNRAR_TOOL = check_setting_str(CFG, 'General', 'unrar_tool', rarfile.UNRAR_TOOL)
        if UNRAR_TOOL:
            rarfile.UNRAR_TOOL = rarfile.ORIG_UNRAR_TOOL = UNRAR_TOOL

        ALT_UNRAR_TOOL = check_setting_str(CFG, 'General', 'alt_unrar_tool', rarfile.ALT_TOOL)
        if ALT_UNRAR_TOOL:
            rarfile.ALT_TOOL = ALT_UNRAR_TOOL

        RENAME_EPISODES = check_setting_bool(CFG, 'General', 'rename_episodes', True)
        AIRDATE_EPISODES = check_setting_bool(CFG, 'General', 'airdate_episodes')
        FILE_TIMESTAMP_TIMEZONE = check_setting_str(CFG, 'General', 'file_timestamp_timezone', 'network')
        KEEP_PROCESSED_DIR = check_setting_bool(CFG, 'General', 'keep_processed_dir', True)
        PROCESS_METHOD = check_setting_str(CFG, 'General', 'process_method', 'copy' if KEEP_PROCESSED_DIR else 'move')
        DELRARCONTENTS = check_setting_bool(CFG, 'General', 'del_rar_contents')
        MOVE_ASSOCIATED_FILES = check_setting_bool(CFG, 'General', 'move_associated_files')
        DELETE_NON_ASSOCIATED_FILES = check_setting_bool(CFG, 'General', 'delete_non_associated_files', True)
        POSTPONE_IF_SYNC_FILES = check_setting_bool(CFG, 'General', 'postpone_if_sync_files', True)
        SYNC_FILES = check_setting_str(CFG, 'General', 'sync_files', SYNC_FILES)
        NFO_RENAME = check_setting_bool(CFG, 'General', 'nfo_rename', True)
        CREATE_MISSING_SHOW_DIRS = check_setting_bool(CFG, 'General', 'create_missing_show_dirs')
        ADD_SHOWS_WO_DIR = check_setting_bool(CFG, 'General', 'add_shows_wo_dir')
        USE_FREE_SPACE_CHECK = check_setting_bool(CFG, 'General', 'use_free_space_check', True)

        NZBS = check_setting_bool(CFG, 'NZBs', 'nzbs')
        NZBS_UID = check_setting_str(CFG, 'NZBs', 'nzbs_uid', censor_log=True)
        NZBS_HASH = check_setting_str(CFG, 'NZBs', 'nzbs_hash', censor_log=True)

        NEWZBIN = check_setting_bool(CFG, 'Newzbin', 'newzbin')
        NEWZBIN_USERNAME = check_setting_str(CFG, 'Newzbin', 'newzbin_username', censor_log=True)
        NEWZBIN_PASSWORD = check_setting_str(CFG, 'Newzbin', 'newzbin_password', censor_log=True)

        SAB_USERNAME = check_setting_str(CFG, 'SABnzbd', 'sab_username', censor_log=True)
        SAB_PASSWORD = check_setting_str(CFG, 'SABnzbd', 'sab_password', censor_log=True)
        SAB_APIKEY = check_setting_str(CFG, 'SABnzbd', 'sab_apikey', censor_log=True)
        SAB_CATEGORY = check_setting_str(CFG, 'SABnzbd', 'sab_category', 'tv')
        SAB_CATEGORY_BACKLOG = check_setting_str(CFG, 'SABnzbd', 'sab_category_backlog', SAB_CATEGORY)
        SAB_CATEGORY_ANIME = check_setting_str(CFG, 'SABnzbd', 'sab_category_anime', 'anime')
        SAB_CATEGORY_ANIME_BACKLOG = check_setting_str(CFG, 'SABnzbd', 'sab_category_anime_backlog', SAB_CATEGORY_ANIME)
        SAB_HOST = check_setting_str(CFG, 'SABnzbd', 'sab_host')
        SAB_FORCED = check_setting_bool(CFG, 'SABnzbd', 'sab_forced')

        NZBGET_USERNAME = check_setting_str(CFG, 'NZBget', 'nzbget_username', 'nzbget', censor_log=True)
        NZBGET_PASSWORD = check_setting_str(CFG, 'NZBget', 'nzbget_password', 'tegbzn6789', censor_log=True)
        NZBGET_CATEGORY = check_setting_str(CFG, 'NZBget', 'nzbget_category', 'tv')
        NZBGET_CATEGORY_BACKLOG = check_setting_str(CFG, 'NZBget', 'nzbget_category_backlog', NZBGET_CATEGORY)
        NZBGET_CATEGORY_ANIME = check_setting_str(CFG, 'NZBget', 'nzbget_category_anime', 'anime')
        NZBGET_CATEGORY_ANIME_BACKLOG = check_setting_str(CFG, 'NZBget', 'nzbget_category_anime_backlog', NZBGET_CATEGORY_ANIME)
        NZBGET_HOST = check_setting_str(CFG, 'NZBget', 'nzbget_host')
        NZBGET_USE_HTTPS = check_setting_bool(CFG, 'NZBget', 'nzbget_use_https')
        NZBGET_PRIORITY = check_setting_int(CFG, 'NZBget', 'nzbget_priority', 100)

        TORRENT_USERNAME = check_setting_str(CFG, 'TORRENT', 'torrent_username', censor_log=True)
        TORRENT_PASSWORD = check_setting_str(CFG, 'TORRENT', 'torrent_password', censor_log=True)
        TORRENT_HOST = check_setting_str(CFG, 'TORRENT', 'torrent_host')
        TORRENT_PATH = check_setting_str(CFG, 'TORRENT', 'torrent_path')
        TORRENT_SEED_TIME = check_setting_int(CFG, 'TORRENT', 'torrent_seed_time')
        TORRENT_PAUSED = check_setting_bool(CFG, 'TORRENT', 'torrent_paused')
        TORRENT_HIGH_BANDWIDTH = check_setting_bool(CFG, 'TORRENT', 'torrent_high_bandwidth')
        TORRENT_LABEL = check_setting_str(CFG, 'TORRENT', 'torrent_label')
        TORRENT_LABEL_ANIME = check_setting_str(CFG, 'TORRENT', 'torrent_label_anime')
        TORRENT_VERIFY_CERT = check_setting_bool(CFG, 'TORRENT', 'torrent_verify_cert')
        TORRENT_RPCURL = check_setting_str(CFG, 'TORRENT', 'torrent_rpcurl', 'transmission')
        TORRENT_AUTH_TYPE = check_setting_str(CFG, 'TORRENT', 'torrent_auth_type')

        SYNOLOGY_DSM_HOST = check_setting_str(CFG, 'Synology', 'host')
        SYNOLOGY_DSM_USERNAME = check_setting_str(CFG, 'Synology', 'username', censor_log=True)
        SYNOLOGY_DSM_PASSWORD = check_setting_str(CFG, 'Synology', 'password', censor_log=True)
        SYNOLOGY_DSM_PATH = check_setting_str(CFG, 'Synology', 'path')

        USE_KODI = check_setting_bool(CFG, 'KODI', 'use_kodi')
        KODI_ALWAYS_ON = check_setting_bool(CFG, 'KODI', 'kodi_always_on', True)
        KODI_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'KODI', 'kodi_notify_onsnatch')
        KODI_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'KODI', 'kodi_notify_ondownload')
        KODI_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'KODI', 'kodi_notify_onsubtitledownload')
        KODI_UPDATE_LIBRARY = check_setting_bool(CFG, 'KODI', 'kodi_update_library')
        KODI_UPDATE_FULL = check_setting_bool(CFG, 'KODI', 'kodi_update_full')
        KODI_UPDATE_ONLYFIRST = check_setting_bool(CFG, 'KODI', 'kodi_update_onlyfirst')
        KODI_HOST = check_setting_str(CFG, 'KODI', 'kodi_host')
        KODI_USERNAME = check_setting_str(CFG, 'KODI', 'kodi_username', censor_log=True)
        KODI_PASSWORD = check_setting_str(CFG, 'KODI', 'kodi_password', censor_log=True)

        USE_PLEX_SERVER = check_setting_bool(CFG, 'Plex', 'use_plex_server')
        PLEX_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Plex', 'plex_notify_onsnatch')
        PLEX_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Plex', 'plex_notify_ondownload')
        PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Plex', 'plex_notify_onsubtitledownload')
        PLEX_UPDATE_LIBRARY = check_setting_bool(CFG, 'Plex', 'plex_update_library')
        PLEX_SERVER_HOST = check_setting_str(CFG, 'Plex', 'plex_server_host')
        PLEX_SERVER_TOKEN = check_setting_str(CFG, 'Plex', 'plex_server_token')
        PLEX_CLIENT_HOST = check_setting_str(CFG, 'Plex', 'plex_client_host')
        PLEX_SERVER_USERNAME = check_setting_str(CFG, 'Plex', 'plex_server_username', censor_log=True)
        PLEX_SERVER_PASSWORD = check_setting_str(CFG, 'Plex', 'plex_server_password', censor_log=True)
        USE_PLEX_CLIENT = check_setting_bool(CFG, 'Plex', 'use_plex_client')
        PLEX_CLIENT_USERNAME = check_setting_str(CFG, 'Plex', 'plex_client_username', censor_log=True)
        PLEX_CLIENT_PASSWORD = check_setting_str(CFG, 'Plex', 'plex_client_password', censor_log=True)
        PLEX_SERVER_HTTPS = check_setting_bool(CFG, 'Plex', 'plex_server_https')

        USE_EMBY = check_setting_bool(CFG, 'Emby', 'use_emby')
        EMBY_HOST = check_setting_str(CFG, 'Emby', 'emby_host')
        EMBY_APIKEY = check_setting_str(CFG, 'Emby', 'emby_apikey')

        USE_GROWL = check_setting_bool(CFG, 'Growl', 'use_growl')
        GROWL_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Growl', 'growl_notify_onsnatch')
        GROWL_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Growl', 'growl_notify_ondownload')
        GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Growl', 'growl_notify_onsubtitledownload')
        GROWL_HOST = check_setting_str(CFG, 'Growl', 'growl_host')
        GROWL_PASSWORD = check_setting_str(CFG, 'Growl', 'growl_password', censor_log=True)

        USE_FREEMOBILE = check_setting_bool(CFG, 'FreeMobile', 'use_freemobile')
        FREEMOBILE_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'FreeMobile', 'freemobile_notify_onsnatch')
        FREEMOBILE_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'FreeMobile', 'freemobile_notify_ondownload')
        FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'FreeMobile', 'freemobile_notify_onsubtitledownload')
        FREEMOBILE_ID = check_setting_str(CFG, 'FreeMobile', 'freemobile_id')
        FREEMOBILE_APIKEY = check_setting_str(CFG, 'FreeMobile', 'freemobile_apikey')

        USE_TELEGRAM = check_setting_bool(CFG, 'Telegram', 'use_telegram')
        TELEGRAM_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Telegram', 'telegram_notify_onsnatch')
        TELEGRAM_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Telegram', 'telegram_notify_ondownload')
        TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Telegram', 'telegram_notify_onsubtitledownload')
        TELEGRAM_ID = check_setting_str(CFG, 'Telegram', 'telegram_id')
        TELEGRAM_APIKEY = check_setting_str(CFG, 'Telegram', 'telegram_apikey')

        USE_JOIN = check_setting_bool(CFG, 'Join', 'use_join')
        JOIN_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Join', 'join_notify_onsnatch')
        JOIN_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Join', 'join_notify_ondownload')
        JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Join', 'join_notify_onsubtitledownload')
        JOIN_ID = check_setting_str(CFG, 'Join', 'join_id')

        USE_PROWL = check_setting_bool(CFG, 'Prowl', 'use_prowl')
        PROWL_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Prowl', 'prowl_notify_onsnatch')
        PROWL_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Prowl', 'prowl_notify_ondownload')
        PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Prowl', 'prowl_notify_onsubtitledownload')
        PROWL_API = check_setting_str(CFG, 'Prowl', 'prowl_api', censor_log=True)
        PROWL_PRIORITY = check_setting_str(CFG, 'Prowl', 'prowl_priority', "0")
        PROWL_MESSAGE_TITLE = check_setting_str(CFG, 'Prowl', 'prowl_message_title', "SickRage")

        USE_TWITTER = check_setting_bool(CFG, 'Twitter', 'use_twitter')
        TWITTER_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Twitter', 'twitter_notify_onsnatch')
        TWITTER_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Twitter', 'twitter_notify_ondownload')
        TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Twitter', 'twitter_notify_onsubtitledownload')
        TWITTER_USERNAME = check_setting_str(CFG, 'Twitter', 'twitter_username', censor_log=True)
        TWITTER_PASSWORD = check_setting_str(CFG, 'Twitter', 'twitter_password', censor_log=True)
        TWITTER_PREFIX = check_setting_str(CFG, 'Twitter', 'twitter_prefix', GIT_REPO)
        TWITTER_DMTO = check_setting_str(CFG, 'Twitter', 'twitter_dmto')
        TWITTER_USEDM = check_setting_bool(CFG, 'Twitter', 'twitter_usedm')

        USE_TWILIO = check_setting_bool(CFG, 'Twilio', 'use_twilio')
        TWILIO_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Twilio', 'twilio_notify_onsnatch')
        TWILIO_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Twilio', 'twilio_notify_ondownload')
        TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Twilio', 'twilio_notify_onsubtitledownload')
        TWILIO_PHONE_SID = check_setting_str(CFG, 'Twilio', 'twilio_phone_sid', censor_log=True)
        TWILIO_ACCOUNT_SID = check_setting_str(CFG, 'Twilio', 'twilio_account_sid', censor_log=True)
        TWILIO_AUTH_TOKEN = check_setting_str(CFG, 'Twilio', 'twilio_auth_token', censor_log=True)
        TWILIO_TO_NUMBER = check_setting_str(CFG, 'Twilio', 'twilio_to_number', censor_log=True)

        USE_BOXCAR2 = check_setting_bool(CFG, 'Boxcar2', 'use_boxcar2')
        BOXCAR2_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Boxcar2', 'boxcar2_notify_onsnatch')
        BOXCAR2_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Boxcar2', 'boxcar2_notify_ondownload')
        BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Boxcar2', 'boxcar2_notify_onsubtitledownload')
        BOXCAR2_ACCESSTOKEN = check_setting_str(CFG, 'Boxcar2', 'boxcar2_accesstoken', censor_log=True)

        USE_PUSHOVER = check_setting_bool(CFG, 'Pushover', 'use_pushover')
        PUSHOVER_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Pushover', 'pushover_notify_onsnatch')
        PUSHOVER_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Pushover', 'pushover_notify_ondownload')
        PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Pushover', 'pushover_notify_onsubtitledownload')
        PUSHOVER_USERKEY = check_setting_str(CFG, 'Pushover', 'pushover_userkey', censor_log=True)
        PUSHOVER_APIKEY = check_setting_str(CFG, 'Pushover', 'pushover_apikey', censor_log=True)
        PUSHOVER_DEVICE = check_setting_str(CFG, 'Pushover', 'pushover_device')
        PUSHOVER_SOUND = check_setting_str(CFG, 'Pushover', 'pushover_sound', 'pushover')
        PUSHOVER_PRIORITY = check_setting_str(CFG, 'Pushover', 'pushover_priority', "0")

        USE_LIBNOTIFY = check_setting_bool(CFG, 'Libnotify', 'use_libnotify')
        LIBNOTIFY_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Libnotify', 'libnotify_notify_onsnatch')
        LIBNOTIFY_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Libnotify', 'libnotify_notify_ondownload')
        LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Libnotify', 'libnotify_notify_onsubtitledownload')

        USE_NMJ = check_setting_bool(CFG, 'NMJ', 'use_nmj')
        NMJ_HOST = check_setting_str(CFG, 'NMJ', 'nmj_host')
        NMJ_DATABASE = check_setting_str(CFG, 'NMJ', 'nmj_database')
        NMJ_MOUNT = check_setting_str(CFG, 'NMJ', 'nmj_mount')

        USE_NMJv2 = check_setting_bool(CFG, 'NMJv2', 'use_nmjv2')
        NMJv2_HOST = check_setting_str(CFG, 'NMJv2', 'nmjv2_host')
        NMJv2_DATABASE = check_setting_str(CFG, 'NMJv2', 'nmjv2_database')
        NMJv2_DBLOC = check_setting_str(CFG, 'NMJv2', 'nmjv2_dbloc')

        USE_SYNOINDEX = check_setting_bool(CFG, 'Synology', 'use_synoindex')

        USE_SYNOLOGYNOTIFIER = check_setting_bool(CFG, 'SynologyNotifier', 'use_synologynotifier')
        SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'SynologyNotifier', 'synologynotifier_notify_onsnatch')
        SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'SynologyNotifier', 'synologynotifier_notify_ondownload')
        SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'SynologyNotifier', 'synologynotifier_notify_onsubtitledownload')

        USE_SLACK = check_setting_bool(CFG, 'Slack', 'use_slack')
        SLACK_NOTIFY_SNATCH = check_setting_bool(CFG, 'Slack', 'slack_notify_snatch')
        SLACK_NOTIFY_DOWNLOAD = check_setting_bool(CFG, 'Slack', 'slack_notify_download')
        SLACK_WEBHOOK = check_setting_str(CFG, 'Slack', 'slack_webhook')

        USE_DISCORD = check_setting_bool(CFG, 'Discord', 'use_discord')
        DISCORD_NOTIFY_SNATCH = check_setting_bool(CFG, 'Discord', 'discord_notify_snatch')
        DISCORD_NOTIFY_DOWNLOAD = check_setting_bool(CFG, 'Discord', 'discord_notify_download')
        DISCORD_WEBHOOK = check_setting_str(CFG, 'Discord', 'discord_webhook')

        USE_TRAKT = check_setting_bool(CFG, 'Trakt', 'use_trakt')
        TRAKT_USERNAME = check_setting_str(CFG, 'Trakt', 'trakt_username', censor_log=True)
        TRAKT_ACCESS_TOKEN = check_setting_str(CFG, 'Trakt', 'trakt_access_token', censor_log=True)
        TRAKT_REFRESH_TOKEN = check_setting_str(CFG, 'Trakt', 'trakt_refresh_token', censor_log=True)
        TRAKT_REMOVE_WATCHLIST = check_setting_bool(CFG, 'Trakt', 'trakt_remove_watchlist')
        TRAKT_REMOVE_SERIESLIST = check_setting_bool(CFG, 'Trakt', 'trakt_remove_serieslist')
        TRAKT_REMOVE_SHOW_FROM_SICKRAGE = check_setting_bool(CFG, 'Trakt', 'trakt_remove_show_from_sickrage')
        TRAKT_SYNC_WATCHLIST = check_setting_bool(CFG, 'Trakt', 'trakt_sync_watchlist')
        TRAKT_METHOD_ADD = check_setting_int(CFG, 'Trakt', 'trakt_method_add')
        TRAKT_START_PAUSED = check_setting_bool(CFG, 'Trakt', 'trakt_start_paused')
        TRAKT_USE_RECOMMENDED = check_setting_bool(CFG, 'Trakt', 'trakt_use_recommended')
        TRAKT_SYNC = check_setting_bool(CFG, 'Trakt', 'trakt_sync')
        TRAKT_SYNC_REMOVE = check_setting_bool(CFG, 'Trakt', 'trakt_sync_remove')
        TRAKT_DEFAULT_INDEXER = check_setting_int(CFG, 'Trakt', 'trakt_default_indexer', 1)
        TRAKT_TIMEOUT = check_setting_int(CFG, 'Trakt', 'trakt_timeout', 30)
        TRAKT_BLACKLIST_NAME = check_setting_str(CFG, 'Trakt', 'trakt_blacklist_name')

        USE_PYTIVO = check_setting_bool(CFG, 'pyTivo', 'use_pytivo')
        PYTIVO_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'pyTivo', 'pytivo_notify_onsnatch')
        PYTIVO_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'pyTivo', 'pytivo_notify_ondownload')
        PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'pyTivo', 'pytivo_notify_onsubtitledownload')
        PYTIVO_UPDATE_LIBRARY = check_setting_bool(CFG, 'pyTivo', 'pyTivo_update_library')
        PYTIVO_HOST = check_setting_str(CFG, 'pyTivo', 'pytivo_host')
        PYTIVO_SHARE_NAME = check_setting_str(CFG, 'pyTivo', 'pytivo_share_name')
        PYTIVO_TIVO_NAME = check_setting_str(CFG, 'pyTivo', 'pytivo_tivo_name')

        USE_NMA = check_setting_bool(CFG, 'NMA', 'use_nma')
        NMA_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'NMA', 'nma_notify_onsnatch')
        NMA_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'NMA', 'nma_notify_ondownload')
        NMA_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'NMA', 'nma_notify_onsubtitledownload')
        NMA_API = check_setting_str(CFG, 'NMA', 'nma_api', censor_log=True)
        NMA_PRIORITY = check_setting_str(CFG, 'NMA', 'nma_priority', "0")

        USE_PUSHALOT = check_setting_bool(CFG, 'Pushalot', 'use_pushalot')
        PUSHALOT_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Pushalot', 'pushalot_notify_onsnatch')
        PUSHALOT_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Pushalot', 'pushalot_notify_ondownload')
        PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Pushalot', 'pushalot_notify_onsubtitledownload')
        PUSHALOT_AUTHORIZATIONTOKEN = check_setting_str(CFG, 'Pushalot', 'pushalot_authorizationtoken', censor_log=True)

        USE_PUSHBULLET = check_setting_bool(CFG, 'Pushbullet', 'use_pushbullet')
        PUSHBULLET_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Pushbullet', 'pushbullet_notify_onsnatch')
        PUSHBULLET_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Pushbullet', 'pushbullet_notify_ondownload')
        PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Pushbullet', 'pushbullet_notify_onsubtitledownload')
        PUSHBULLET_API = check_setting_str(CFG, 'Pushbullet', 'pushbullet_api', censor_log=True)
        PUSHBULLET_DEVICE = check_setting_str(CFG, 'Pushbullet', 'pushbullet_device')
        PUSHBULLET_CHANNEL = check_setting_str(CFG, 'Pushbullet', 'pushbullet_channel')

        USE_EMAIL = check_setting_bool(CFG, 'Email', 'use_email')
        EMAIL_NOTIFY_ONSNATCH = check_setting_bool(CFG, 'Email', 'email_notify_onsnatch')
        EMAIL_NOTIFY_ONDOWNLOAD = check_setting_bool(CFG, 'Email', 'email_notify_ondownload')
        EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = check_setting_bool(CFG, 'Email', 'email_notify_onsubtitledownload')
        EMAIL_HOST = check_setting_str(CFG, 'Email', 'email_host')
        EMAIL_PORT = check_setting_int(CFG, 'Email', 'email_port', 25)
        EMAIL_TLS = check_setting_bool(CFG, 'Email', 'email_tls')
        EMAIL_USER = check_setting_str(CFG, 'Email', 'email_user', censor_log=True)
        EMAIL_PASSWORD = check_setting_str(CFG, 'Email', 'email_password', censor_log=True)
        EMAIL_FROM = check_setting_str(CFG, 'Email', 'email_from')
        EMAIL_LIST = check_setting_str(CFG, 'Email', 'email_list')
        EMAIL_SUBJECT = check_setting_str(CFG, 'Email', 'email_subject')

        USE_SUBTITLES = check_setting_bool(CFG, 'Subtitles', 'use_subtitles')
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
        SUBTITLES_FINDER_FREQUENCY = check_setting_int(CFG, 'Subtitles', 'subtitles_finder_frequency', 1)
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

        USE_FAILED_DOWNLOADS = check_setting_bool(CFG, 'FailedDownloads', 'use_failed_downloads')
        DELETE_FAILED = check_setting_bool(CFG, 'FailedDownloads', 'delete_failed')

        GIT_PATH = check_setting_str(CFG, 'General', 'git_path')

        IGNORE_WORDS = check_setting_str(CFG, 'General', 'ignore_words', IGNORE_WORDS)
        TRACKERS_LIST = check_setting_str(CFG, 'General', 'trackers_list', TRACKERS_LIST)
        REQUIRE_WORDS = check_setting_str(CFG, 'General', 'require_words', REQUIRE_WORDS)
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
        DISPLAY_SHOW_SPECIALS = check_setting_bool(CFG, 'GUI', 'display_show_specials', True)
        COMING_EPS_LAYOUT = check_setting_str(CFG, 'GUI', 'coming_eps_layout', 'banner')
        COMING_EPS_DISPLAY_PAUSED = check_setting_bool(CFG, 'GUI', 'coming_eps_display_paused')
        COMING_EPS_SORT = check_setting_str(CFG, 'GUI', 'coming_eps_sort', 'date')
        COMING_EPS_MISSED_RANGE = check_setting_int(CFG, 'GUI', 'coming_eps_missed_range', 7)
        FUZZY_DATING = check_setting_bool(CFG, 'GUI', 'fuzzy_dating')
        TRIM_ZERO = check_setting_bool(CFG, 'GUI', 'trim_zero')
        DATE_PRESET = check_setting_str(CFG, 'GUI', 'date_preset', '%x')
        TIME_PRESET_W_SECONDS = check_setting_str(CFG, 'GUI', 'time_preset', '%I:%M:%S %p')
        TIME_PRESET = TIME_PRESET_W_SECONDS.replace(u":%S", u"")
        TIMEZONE_DISPLAY = check_setting_str(CFG, 'GUI', 'timezone_display', 'local')
        POSTER_SORTBY = check_setting_str(CFG, 'GUI', 'poster_sortby', 'name')
        POSTER_SORTDIR = check_setting_int(CFG, 'GUI', 'poster_sortdir', 1)
        DISPLAY_ALL_SEASONS = check_setting_bool(CFG, 'General', 'display_all_seasons', True)

        # initialize NZB and TORRENT providers
        providerList = providers.makeProviderList()

        NEWZNAB_DATA = check_setting_str(CFG, 'Newznab', 'newznab_data')
        newznabProviderList = NewznabProvider.get_providers_list(NEWZNAB_DATA)

        TORRENTRSS_DATA = check_setting_str(CFG, 'TorrentRss', 'torrentrss_data')
        torrentRssProviderList = TorrentRssProvider.get_providers_list(TORRENTRSS_DATA)

        # dynamically load provider settings
        for curTorrentProvider in [curProvider for curProvider in providers.sortedProviderList() if
                                   curProvider.provider_type == GenericProvider.TORRENT]:
            curTorrentProvider.enabled = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id())
            if hasattr(curTorrentProvider, 'custom_url'):
                curTorrentProvider.custom_url = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                                  curTorrentProvider.get_id() + '_custom_url',
                                                                  '', censor_log=True)
            if hasattr(curTorrentProvider, 'api_key'):
                curTorrentProvider.api_key = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_api_key', censor_log=True)
            if hasattr(curTorrentProvider, 'hash'):
                curTorrentProvider.hash = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                            curTorrentProvider.get_id() + '_hash', censor_log=True)
            if hasattr(curTorrentProvider, 'digest'):
                curTorrentProvider.digest = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                              curTorrentProvider.get_id() + '_digest', censor_log=True)
            if hasattr(curTorrentProvider, 'username'):
                curTorrentProvider.username = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                                curTorrentProvider.get_id() + '_username', censor_log=True)
            if hasattr(curTorrentProvider, 'password'):
                curTorrentProvider.password = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                                curTorrentProvider.get_id() + '_password', censor_log=True)
            if hasattr(curTorrentProvider, 'passkey'):
                curTorrentProvider.passkey = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_passkey', censor_log=True)
            if hasattr(curTorrentProvider, 'pin'):
                curTorrentProvider.pin = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                           curTorrentProvider.get_id() + '_pin', censor_log=True)
            if hasattr(curTorrentProvider, 'confirmed'):
                curTorrentProvider.confirmed = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_confirmed', True)

            if hasattr(curTorrentProvider, 'ranked'):
                curTorrentProvider.ranked = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_ranked', True)

            if hasattr(curTorrentProvider, 'engrelease'):
                curTorrentProvider.engrelease = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_engrelease')

            if hasattr(curTorrentProvider, 'onlyspasearch'):
                curTorrentProvider.onlyspasearch = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_onlyspasearch')

            if hasattr(curTorrentProvider, 'sorting'):
                curTorrentProvider.sorting = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_sorting', 'seeders')
            if hasattr(curTorrentProvider, 'options'):
                curTorrentProvider.options = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_options', '')
            if hasattr(curTorrentProvider, 'ratio'):
                curTorrentProvider.ratio = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                             curTorrentProvider.get_id() + '_ratio', '')
            if hasattr(curTorrentProvider, 'minseed'):
                curTorrentProvider.minseed = check_setting_int(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_minseed', 1)
            if hasattr(curTorrentProvider, 'minleech'):
                curTorrentProvider.minleech = check_setting_int(CFG, curTorrentProvider.get_id().upper(),
                                                                curTorrentProvider.get_id() + '_minleech', 0)
            if hasattr(curTorrentProvider, 'freeleech'):
                curTorrentProvider.freeleech = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_freeleech')
            if hasattr(curTorrentProvider, 'search_mode'):
                curTorrentProvider.search_mode = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                                   curTorrentProvider.get_id() + '_search_mode',
                                                                   'eponly')
            if hasattr(curTorrentProvider, 'search_fallback'):
                curTorrentProvider.search_fallback = check_setting_bool(CFG, curTorrentProvider.get_id().upper(),
                                                                            curTorrentProvider.get_id() + '_search_fallback')

            if hasattr(curTorrentProvider, 'enable_daily'):
                curTorrentProvider.enable_daily = check_setting_bool(CFG, curTorrentProvider.get_id().upper(),
                                                                         curTorrentProvider.get_id() + '_enable_daily', True)

            if hasattr(curTorrentProvider, 'enable_backlog'):
                curTorrentProvider.enable_backlog = check_setting_bool(CFG, curTorrentProvider.get_id().upper(),
                                                                           curTorrentProvider.get_id() + '_enable_backlog',
                                                                           curTorrentProvider.supports_backlog)

            if hasattr(curTorrentProvider, 'cat'):
                curTorrentProvider.cat = check_setting_int(CFG, curTorrentProvider.get_id().upper(),
                                                           curTorrentProvider.get_id() + '_cat', 0)
            if hasattr(curTorrentProvider, 'subtitle'):
                curTorrentProvider.subtitle = check_setting_bool(CFG, curTorrentProvider.get_id().upper(), curTorrentProvider.get_id() + '_subtitle')

            if hasattr(curTorrentProvider, 'cookies'):
                curTorrentProvider.cookies = check_setting_str(CFG, curTorrentProvider.get_id().upper(),
                                                               curTorrentProvider.get_id() + '_cookies', censor_log=True)

        for curNzbProvider in [curProvider for curProvider in providers.sortedProviderList() if
                               curProvider.provider_type == GenericProvider.NZB]:
            curNzbProvider.enabled = check_setting_bool(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id())

            if hasattr(curNzbProvider, 'api_key'):
                curNzbProvider.api_key = check_setting_str(CFG, curNzbProvider.get_id().upper(),
                                                           curNzbProvider.get_id() + '_api_key', censor_log=True)

            if hasattr(curNzbProvider, 'username'):
                curNzbProvider.username = check_setting_str(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id() + '_username', censor_log=True)
            if hasattr(curNzbProvider, 'search_mode'):
                curNzbProvider.search_mode = check_setting_str(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id() + '_search_mode', 'eponly')

            if hasattr(curNzbProvider, 'search_fallback'):
                curNzbProvider.search_fallback = check_setting_bool(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id() + '_search_fallback')

            if hasattr(curNzbProvider, 'enable_daily'):
                curNzbProvider.enable_daily = check_setting_bool(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id() + '_enable_daily', True)

            if hasattr(curNzbProvider, 'enable_backlog'):
                curNzbProvider.enable_backlog = check_setting_bool(CFG, curNzbProvider.get_id().upper(), curNzbProvider.get_id() + '_enable_backlog',
                                                                  curNzbProvider.supports_backlog)

        if not ek(os.path.isfile, CONFIG_FILE):
            logger.log(u"Unable to find '" + CONFIG_FILE + "', all settings will be default!", logger.DEBUG)
            save_config()

        # initialize the main SB database
        main_db_con = db.DBConnection()
        db.upgradeDatabase(main_db_con, mainDB.InitialSchema)

        # initialize the cache database
        cache_db_con = db.DBConnection('cache.db')
        db.upgradeDatabase(cache_db_con, cache_db.InitialSchema)

        # initialize the failed downloads database
        failed_db_con = db.DBConnection('failed.db')
        db.upgradeDatabase(failed_db_con, failed_db.InitialSchema)

        # fix up any db problems
        main_db_con = db.DBConnection()
        db.sanityCheckDatabase(main_db_con, mainDB.MainSanityCheck)

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
            showUpdater.ShowUpdater(),
            run_delay=datetime.timedelta(seconds=20),
            cycleTime=datetime.timedelta(hours=1),
            start_time=datetime.time(hour=SHOWUPDATE_HOUR),
            threadName="SHOWUPDATER"
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
            auto_postprocessor.PostProcessor(),
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

            # start the trakt checker
            traktCheckerScheduler.enable = USE_TRAKT
            traktCheckerScheduler.start()

            started['0'] = True


def halt():
    with INIT_LOCK:
        if __INITIALIZED__:
            logger.log(u"Aborting all threads")

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
                events
            ]

            # set them all to stop at the same time
            for t in threads:
                t.stop.set()

            for t in threads:
                logger.log(u"Waiting for the {0} thread to exit".format(t.name))
                try:
                    t.join(10)
                except Exception:
                    pass

            if ADBA_CONNECTION:
                ADBA_CONNECTION.logout()
                logger.log(u"Waiting for the ANIDB CONNECTION thread to exit")
                try:
                    ADBA_CONNECTION.join(10)
                except Exception:
                    pass

            __INITIALIZED__.clear()
        started.clear()


def sig_handler(signum=None, frame=None):
    frame_ = frame
    if not isinstance(signum, type(None)):
        logger.log(u"Signal {0:d} caught, saving and exiting...".format(int(signum)))
        Shutdown.stop(PID)


def saveAll():
    # write all shows
    logger.log(u"Saving all shows to the database")
    for show in showList:
        show.saveToDB()

    # save config
    logger.log(u"Saving config file to disk")
    save_config()


def save_config():  # pylint: disable=too-many-statements, too-many-branches
    new_config = ConfigObj(CONFIG_FILE, encoding='UTF-8')

    # For passwords you must include the word `password` in the item_name and add `helpers.encrypt(ITEM_NAME, ENCRYPTION_VERSION)` in save_config()
    # dynamically save provider settings
    for curTorrentProvider in [curProvider for curProvider in providers.sortedProviderList() if
                               curProvider.provider_type == GenericProvider.TORRENT]:
        new_config[curTorrentProvider.get_id().upper()] = {}
        new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id()] = int(curTorrentProvider.enabled)
        if hasattr(curTorrentProvider, 'custom_url'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_custom_url'] = curTorrentProvider.custom_url
        if hasattr(curTorrentProvider, 'digest'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_digest'] = curTorrentProvider.digest
        if hasattr(curTorrentProvider, 'hash'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_hash'] = curTorrentProvider.hash
        if hasattr(curTorrentProvider, 'api_key'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_api_key'] = curTorrentProvider.api_key
        if hasattr(curTorrentProvider, 'username'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_username'] = curTorrentProvider.username
        if hasattr(curTorrentProvider, 'password'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_password'] = helpers.encrypt(
                curTorrentProvider.password, ENCRYPTION_VERSION)
        if hasattr(curTorrentProvider, 'passkey'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_passkey'] = curTorrentProvider.passkey
        if hasattr(curTorrentProvider, 'pin'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_pin'] = curTorrentProvider.pin
        if hasattr(curTorrentProvider, 'confirmed'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_confirmed'] = int(
                curTorrentProvider.confirmed)
        if hasattr(curTorrentProvider, 'ranked'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_ranked'] = int(
                curTorrentProvider.ranked)
        if hasattr(curTorrentProvider, 'engrelease'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_engrelease'] = int(
                curTorrentProvider.engrelease)
        if hasattr(curTorrentProvider, 'onlyspasearch'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_onlyspasearch'] = int(
                curTorrentProvider.onlyspasearch)
        if hasattr(curTorrentProvider, 'sorting'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_sorting'] = curTorrentProvider.sorting
        if hasattr(curTorrentProvider, 'ratio'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_ratio'] = curTorrentProvider.ratio
        if hasattr(curTorrentProvider, 'minseed'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_minseed'] = int(
                curTorrentProvider.minseed)
        if hasattr(curTorrentProvider, 'minleech'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_minleech'] = int(
                curTorrentProvider.minleech)
        if hasattr(curTorrentProvider, 'options'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_options'] = curTorrentProvider.options
        if hasattr(curTorrentProvider, 'freeleech'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_freeleech'] = int(
                curTorrentProvider.freeleech)
        if hasattr(curTorrentProvider, 'search_mode'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_search_mode'] = curTorrentProvider.search_mode
        if hasattr(curTorrentProvider, 'search_fallback'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_search_fallback'] = int(
                curTorrentProvider.search_fallback)
        if hasattr(curTorrentProvider, 'enable_daily'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_enable_daily'] = int(
                curTorrentProvider.enable_daily)
        if hasattr(curTorrentProvider, 'enable_backlog'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_enable_backlog'] = int(
                curTorrentProvider.enable_backlog)
        if hasattr(curTorrentProvider, 'cat'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_cat'] = int(
                curTorrentProvider.cat)
        if hasattr(curTorrentProvider, 'subtitle'):
            new_config[curTorrentProvider.get_id().upper()][curTorrentProvider.get_id() + '_subtitle'] = int(
                curTorrentProvider.subtitle)
        if hasattr(curTorrentProvider, 'cookies'):
            new_config[curTorrentProvider.get_id().upper()][
                curTorrentProvider.get_id() + '_cookies'] = curTorrentProvider.cookies

    for curNzbProvider in [curProvider for curProvider in providers.sortedProviderList() if
                           curProvider.provider_type == GenericProvider.NZB]:
        new_config[curNzbProvider.get_id().upper()] = {}
        new_config[curNzbProvider.get_id().upper()][curNzbProvider.get_id()] = int(curNzbProvider.enabled)

        if hasattr(curNzbProvider, 'api_key'):
            new_config[curNzbProvider.get_id().upper()][
                curNzbProvider.get_id() + '_api_key'] = curNzbProvider.api_key
        if hasattr(curNzbProvider, 'username'):
            new_config[curNzbProvider.get_id().upper()][
                curNzbProvider.get_id() + '_username'] = curNzbProvider.username
        if hasattr(curNzbProvider, 'search_mode'):
            new_config[curNzbProvider.get_id().upper()][
                curNzbProvider.get_id() + '_search_mode'] = curNzbProvider.search_mode
        if hasattr(curNzbProvider, 'search_fallback'):
            new_config[curNzbProvider.get_id().upper()][curNzbProvider.get_id() + '_search_fallback'] = int(
                curNzbProvider.search_fallback)
        if hasattr(curNzbProvider, 'enable_daily'):
            new_config[curNzbProvider.get_id().upper()][curNzbProvider.get_id() + '_enable_daily'] = int(
                curNzbProvider.enable_daily)
        if hasattr(curNzbProvider, 'enable_backlog'):
            new_config[curNzbProvider.get_id().upper()][curNzbProvider.get_id() + '_enable_backlog'] = int(
                curNzbProvider.enable_backlog)

    new_config.update({
        'General': {
            'git_auth_type': int(GIT_AUTH_TYPE),
            'git_username': GIT_USERNAME,
            'git_password': helpers.encrypt(GIT_PASSWORD, ENCRYPTION_VERSION),
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
            'log_dir': ACTUAL_LOG_DIR if ACTUAL_LOG_DIR else 'Logs',
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
            'nzb_method': NZB_METHOD,
            'torrent_method': TORRENT_METHOD,
            'usenet_retention': int(USENET_RETENTION),
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
            'sort_article': int(SORT_ARTICLE),
            'proxy_setting': PROXY_SETTING,
            'proxy_indexers': int(PROXY_INDEXERS),
            'use_listview': int(USE_LISTVIEW),

            'metadata_kodi': METADATA_KODI,
            'metadata_kodi_12plus': METADATA_KODI_12PLUS,
            'metadata_mediabrowser': METADATA_MEDIABROWSER,
            'metadata_ps3': METADATA_PS3,
            'metadata_wdtv': METADATA_WDTV,
            'metadata_tivo': METADATA_TIVO,
            'metadata_mede8er': METADATA_MEDE8ER,

            'backlog_days': int(BACKLOG_DAYS),

            'cache_dir': ACTUAL_CACHE_DIR if ACTUAL_CACHE_DIR else 'cache',
            'root_dirs': ROOT_DIRS if ROOT_DIRS else '',
            'tv_download_dir': TV_DOWNLOAD_DIR,
            'keep_processed_dir': int(KEEP_PROCESSED_DIR),
            'process_method': PROCESS_METHOD,
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
            'use_free_space_check': int(USE_FREE_SPACE_CHECK),

            'extra_scripts': '|'.join(EXTRA_SCRIPTS),
            'git_path': GIT_PATH,
            'ignore_words': IGNORE_WORDS,
            'trackers_list': TRACKERS_LIST,
            'require_words': REQUIRE_WORDS,
            'ignored_subs_list': IGNORED_SUBS_LIST,
            'calendar_unprotected': int(CALENDAR_UNPROTECTED),
            'calendar_icons': int(CALENDAR_ICONS),
            'no_restart': int(NO_RESTART),
            'developer': int(DEVELOPER),
            'display_all_seasons': int(DISPLAY_ALL_SEASONS),
            'news_last_read': NEWS_LAST_READ,
        },

        'Blackhole': {
            'nzb_dir': NZB_DIR,
            'torrent_dir': TORRENT_DIR,
        },

        'NZBs': {
            'nzbs': int(NZBS),
            'nzbs_uid': NZBS_UID,
            'nzbs_hash': NZBS_HASH,
        },

        'Newzbin': {
            'newzbin': int(NEWZBIN),
            'newzbin_username': NEWZBIN_USERNAME,
            'newzbin_password': helpers.encrypt(NEWZBIN_PASSWORD, ENCRYPTION_VERSION),
        },

        'SABnzbd': {
            'sab_username': SAB_USERNAME,
            'sab_password': helpers.encrypt(SAB_PASSWORD, ENCRYPTION_VERSION),
            'sab_apikey': SAB_APIKEY,
            'sab_category': SAB_CATEGORY,
            'sab_category_backlog': SAB_CATEGORY_BACKLOG,
            'sab_category_anime': SAB_CATEGORY_ANIME,
            'sab_category_anime_backlog': SAB_CATEGORY_ANIME_BACKLOG,
            'sab_host': SAB_HOST,
            'sab_forced': int(SAB_FORCED),
        },

        'NZBget': {

            'nzbget_username': NZBGET_USERNAME,
            'nzbget_password': helpers.encrypt(NZBGET_PASSWORD, ENCRYPTION_VERSION),
            'nzbget_category': NZBGET_CATEGORY,
            'nzbget_category_backlog': NZBGET_CATEGORY_BACKLOG,
            'nzbget_category_anime': NZBGET_CATEGORY_ANIME,
            'nzbget_category_anime_backlog': NZBGET_CATEGORY_ANIME_BACKLOG,
            'nzbget_host': NZBGET_HOST,
            'nzbget_use_https': int(NZBGET_USE_HTTPS),
            'nzbget_priority': NZBGET_PRIORITY,
        },

        'TORRENT': {
            'torrent_username': TORRENT_USERNAME,
            'torrent_password': helpers.encrypt(TORRENT_PASSWORD, ENCRYPTION_VERSION),
            'torrent_host': TORRENT_HOST,
            'torrent_path': TORRENT_PATH,
            'torrent_seed_time': int(TORRENT_SEED_TIME),
            'torrent_paused': int(TORRENT_PAUSED),
            'torrent_high_bandwidth': int(TORRENT_HIGH_BANDWIDTH),
            'torrent_label': TORRENT_LABEL,
            'torrent_label_anime': TORRENT_LABEL_ANIME,
            'torrent_verify_cert': int(TORRENT_VERIFY_CERT),
            'torrent_rpcurl': TORRENT_RPCURL,
            'torrent_auth_type': TORRENT_AUTH_TYPE,
        },

        'KODI': {
            'use_kodi': int(USE_KODI),
            'kodi_always_on': int(KODI_ALWAYS_ON),
            'kodi_notify_onsnatch': int(KODI_NOTIFY_ONSNATCH),
            'kodi_notify_ondownload': int(KODI_NOTIFY_ONDOWNLOAD),
            'kodi_notify_onsubtitledownload': int(KODI_NOTIFY_ONSUBTITLEDOWNLOAD),
            'kodi_update_library': int(KODI_UPDATE_LIBRARY),
            'kodi_update_full': int(KODI_UPDATE_FULL),
            'kodi_update_onlyfirst': int(KODI_UPDATE_ONLYFIRST),
            'kodi_host': KODI_HOST,
            'kodi_username': KODI_USERNAME,
            'kodi_password': helpers.encrypt(KODI_PASSWORD, ENCRYPTION_VERSION),
        },

        'Plex': {
            'use_plex_server': int(USE_PLEX_SERVER),
            'plex_notify_onsnatch': int(PLEX_NOTIFY_ONSNATCH),
            'plex_notify_ondownload': int(PLEX_NOTIFY_ONDOWNLOAD),
            'plex_notify_onsubtitledownload': int(PLEX_NOTIFY_ONSUBTITLEDOWNLOAD),
            'plex_update_library': int(PLEX_UPDATE_LIBRARY),
            'plex_server_host': PLEX_SERVER_HOST,
            'plex_server_token': PLEX_SERVER_TOKEN,
            'plex_client_host': PLEX_CLIENT_HOST,
            'plex_server_username': PLEX_SERVER_USERNAME,
            'plex_server_password': helpers.encrypt(PLEX_SERVER_PASSWORD, ENCRYPTION_VERSION),

            'use_plex_client': int(USE_PLEX_CLIENT),
            'plex_client_username': PLEX_CLIENT_USERNAME,
            'plex_client_password': helpers.encrypt(PLEX_CLIENT_PASSWORD, ENCRYPTION_VERSION),
            'plex_server_https': int(PLEX_SERVER_HTTPS),
        },

        'Emby': {
            'use_emby': int(USE_EMBY),
            'emby_host': EMBY_HOST,
            'emby_apikey': EMBY_APIKEY,
        },

        'Growl': {
            'use_growl': int(USE_GROWL),
            'growl_notify_onsnatch': int(GROWL_NOTIFY_ONSNATCH),
            'growl_notify_ondownload': int(GROWL_NOTIFY_ONDOWNLOAD),
            'growl_notify_onsubtitledownload': int(GROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
            'growl_host': GROWL_HOST,
            'growl_password': helpers.encrypt(GROWL_PASSWORD, ENCRYPTION_VERSION),
        },

        'FreeMobile': {
            'use_freemobile': int(USE_FREEMOBILE),
            'freemobile_notify_onsnatch': int(FREEMOBILE_NOTIFY_ONSNATCH),
            'freemobile_notify_ondownload': int(FREEMOBILE_NOTIFY_ONDOWNLOAD),
            'freemobile_notify_onsubtitledownload': int(FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD),
            'freemobile_id': FREEMOBILE_ID,
            'freemobile_apikey': FREEMOBILE_APIKEY,
        },

        'Telegram': {
            'use_telegram': int(USE_TELEGRAM),
            'telegram_notify_onsnatch': int(TELEGRAM_NOTIFY_ONSNATCH),
            'telegram_notify_ondownload': int(TELEGRAM_NOTIFY_ONDOWNLOAD),
            'telegram_notify_onsubtitledownload': int(TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD),
            'telegram_id': TELEGRAM_ID,
            'telegram_apikey': TELEGRAM_APIKEY,
        },

        'Join': {
            'use_join': int(USE_JOIN),
            'join_notify_onsnatch': int(JOIN_NOTIFY_ONSNATCH),
            'join_notify_ondownload': int(JOIN_NOTIFY_ONDOWNLOAD),
            'join_notify_onsubtitledownload': int(JOIN_NOTIFY_ONSUBTITLEDOWNLOAD),
            'join_id': JOIN_ID,
        },

        'Prowl': {
            'use_prowl': int(USE_PROWL),
            'prowl_notify_onsnatch': int(PROWL_NOTIFY_ONSNATCH),
            'prowl_notify_ondownload': int(PROWL_NOTIFY_ONDOWNLOAD),
            'prowl_notify_onsubtitledownload': int(PROWL_NOTIFY_ONSUBTITLEDOWNLOAD),
            'prowl_api': PROWL_API,
            'prowl_priority': PROWL_PRIORITY,
            'prowl_message_title': PROWL_MESSAGE_TITLE,
        },

        'Twitter': {
            'use_twitter': int(USE_TWITTER),
            'twitter_notify_onsnatch': int(TWITTER_NOTIFY_ONSNATCH),
            'twitter_notify_ondownload': int(TWITTER_NOTIFY_ONDOWNLOAD),
            'twitter_notify_onsubtitledownload': int(TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD),
            'twitter_username': TWITTER_USERNAME,
            'twitter_password': helpers.encrypt(TWITTER_PASSWORD, ENCRYPTION_VERSION),
            'twitter_prefix': TWITTER_PREFIX,
            'twitter_dmto': TWITTER_DMTO,
            'twitter_usedm': int(TWITTER_USEDM),
        },

        'Twilio': {
            'use_twilio': int(USE_TWILIO),
            'twilio_notify_onsnatch': int(TWILIO_NOTIFY_ONSNATCH),
            'twilio_notify_ondownload': int(TWILIO_NOTIFY_ONDOWNLOAD),
            'twilio_notify_onsubtitledownload': int(TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD),
            'twilio_phone_sid': helpers.encrypt(TWILIO_PHONE_SID, ENCRYPTION_VERSION),
            'twilio_account_sid': helpers.encrypt(TWILIO_ACCOUNT_SID, ENCRYPTION_VERSION),
            'twilio_auth_token': helpers.encrypt(TWILIO_AUTH_TOKEN, ENCRYPTION_VERSION),
            'twilio_to_number': helpers.encrypt(TWILIO_TO_NUMBER, ENCRYPTION_VERSION),
        },

        'Boxcar2': {
            'use_boxcar2': int(USE_BOXCAR2),
            'boxcar2_notify_onsnatch': int(BOXCAR2_NOTIFY_ONSNATCH),
            'boxcar2_notify_ondownload': int(BOXCAR2_NOTIFY_ONDOWNLOAD),
            'boxcar2_notify_onsubtitledownload': int(BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD),
            'boxcar2_accesstoken': BOXCAR2_ACCESSTOKEN,
        },

        'Pushover': {
            'use_pushover': int(USE_PUSHOVER),
            'pushover_notify_onsnatch': int(PUSHOVER_NOTIFY_ONSNATCH),
            'pushover_notify_ondownload': int(PUSHOVER_NOTIFY_ONDOWNLOAD),
            'pushover_notify_onsubtitledownload': int(PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD),
            'pushover_userkey': PUSHOVER_USERKEY,
            'pushover_apikey': PUSHOVER_APIKEY,
            'pushover_device': PUSHOVER_DEVICE,
            'pushover_sound': PUSHOVER_SOUND,
            'pushover_priority': PUSHOVER_PRIORITY,
        },

        'Libnotify': {
            'use_libnotify': int(USE_LIBNOTIFY),
            'libnotify_notify_onsnatch': int(LIBNOTIFY_NOTIFY_ONSNATCH),
            'libnotify_notify_ondownload': int(LIBNOTIFY_NOTIFY_ONDOWNLOAD),
            'libnotify_notify_onsubtitledownload': int(LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD),
        },

        'NMJ': {
            'use_nmj': int(USE_NMJ),
            'nmj_host': NMJ_HOST,
            'nmj_database': NMJ_DATABASE,
            'nmj_mount': NMJ_MOUNT
        },

        'NMJv2': {
            'use_nmjv2': int(USE_NMJv2),
            'nmjv2_host': NMJv2_HOST,
            'nmjv2_database': NMJv2_DATABASE,
            'nmjv2_dbloc': NMJv2_DBLOC
        },

        'Synology': {
            'use_synoindex': int(USE_SYNOINDEX),
            'host': SYNOLOGY_DSM_HOST,
            'username': SYNOLOGY_DSM_USERNAME,
            'password': helpers.encrypt(SYNOLOGY_DSM_PASSWORD, ENCRYPTION_VERSION),
            'path': SYNOLOGY_DSM_PATH
        },

        'SynologyNotifier': {
            'use_synologynotifier': int(USE_SYNOLOGYNOTIFIER),
            'synologynotifier_notify_onsnatch': int(SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH),
            'synologynotifier_notify_ondownload': int(SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD),
            'synologynotifier_notify_onsubtitledownload': int(SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD)
        },

        'Slack': {
            'use_slack': int(USE_SLACK),
            'slack_notify_snatch': int(SLACK_NOTIFY_SNATCH),
            'slack_notify_download': int(SLACK_NOTIFY_DOWNLOAD),
            'slack_webhook': SLACK_WEBHOOK
        },

        'Discord': {
            'use_discord': int(USE_DISCORD),
            'discord_notify_snatch': int(DISCORD_NOTIFY_SNATCH),
            'discord_notify_download': int(DISCORD_NOTIFY_DOWNLOAD),
            'discord_webhook': DISCORD_WEBHOOK
        },

        'Trakt': {
            'use_trakt': int(USE_TRAKT),
            'trakt_username': TRAKT_USERNAME,
            'trakt_access_token': TRAKT_ACCESS_TOKEN,
            'trakt_refresh_token': TRAKT_REFRESH_TOKEN,
            'trakt_remove_watchlist': int(TRAKT_REMOVE_WATCHLIST),
            'trakt_remove_serieslist': int(TRAKT_REMOVE_SERIESLIST),
            'trakt_remove_show_from_sickrage': int(TRAKT_REMOVE_SHOW_FROM_SICKRAGE),
            'trakt_sync_watchlist': int(TRAKT_SYNC_WATCHLIST),
            'trakt_method_add': int(TRAKT_METHOD_ADD),
            'trakt_start_paused': int(TRAKT_START_PAUSED),
            'trakt_use_recommended': int(TRAKT_USE_RECOMMENDED),
            'trakt_sync': int(TRAKT_SYNC),
            'trakt_sync_remove': int(TRAKT_SYNC_REMOVE),
            'trakt_default_indexer': int(TRAKT_DEFAULT_INDEXER),
            'trakt_timeout': int(TRAKT_TIMEOUT),
            'trakt_blacklist_name': TRAKT_BLACKLIST_NAME
        },

        'pyTivo': {
            'use_pytivo': int(USE_PYTIVO),
            'pytivo_notify_onsnatch': int(PYTIVO_NOTIFY_ONSNATCH),
            'pytivo_notify_ondownload': int(PYTIVO_NOTIFY_ONDOWNLOAD),
            'pytivo_notify_onsubtitledownload': int(PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD),
            'pyTivo_update_library': int(PYTIVO_UPDATE_LIBRARY),
            'pytivo_host': PYTIVO_HOST,
            'pytivo_share_name': PYTIVO_SHARE_NAME,
            'pytivo_tivo_name': PYTIVO_TIVO_NAME
        },

        'NMA': {
            'use_nma': int(USE_NMA),
            'nma_notify_onsnatch': int(NMA_NOTIFY_ONSNATCH),
            'nma_notify_ondownload': int(NMA_NOTIFY_ONDOWNLOAD),
            'nma_notify_onsubtitledownload': int(NMA_NOTIFY_ONSUBTITLEDOWNLOAD),
            'nma_api': NMA_API,
            'nma_priority': NMA_PRIORITY
        },

        'Pushalot': {
            'use_pushalot': int(USE_PUSHALOT),
            'pushalot_notify_onsnatch': int(PUSHALOT_NOTIFY_ONSNATCH),
            'pushalot_notify_ondownload': int(PUSHALOT_NOTIFY_ONDOWNLOAD),
            'pushalot_notify_onsubtitledownload': int(PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD),
            'pushalot_authorizationtoken': PUSHALOT_AUTHORIZATIONTOKEN
        },

        'Pushbullet': {
            'use_pushbullet': int(USE_PUSHBULLET),
            'pushbullet_notify_onsnatch': int(PUSHBULLET_NOTIFY_ONSNATCH),
            'pushbullet_notify_ondownload': int(PUSHBULLET_NOTIFY_ONDOWNLOAD),
            'pushbullet_notify_onsubtitledownload': int(PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD),
            'pushbullet_api': PUSHBULLET_API,
            'pushbullet_device': PUSHBULLET_DEVICE,
            'pushbullet_channel': PUSHBULLET_CHANNEL,
        },

        'Email': {
            'use_email': int(USE_EMAIL),
            'email_notify_onsnatch': int(EMAIL_NOTIFY_ONSNATCH),
            'email_notify_ondownload': int(EMAIL_NOTIFY_ONDOWNLOAD),
            'email_notify_onsubtitledownload': int(EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD),
            'email_host': EMAIL_HOST,
            'email_port': int(EMAIL_PORT),
            'email_tls': int(EMAIL_TLS),
            'email_user': EMAIL_USER,
            'email_password': helpers.encrypt(EMAIL_PASSWORD, ENCRYPTION_VERSION),
            'email_from': EMAIL_FROM,
            'email_list': EMAIL_LIST,
            'email_subject': EMAIL_SUBJECT
        },

        'Newznab': {
            'newznab_data': NEWZNAB_DATA
        },

        'TorrentRss': {
            'torrentrss_data': '!!!'.join([x.configStr() for x in torrentRssProviderList])
        },

        'GUI': {
            'gui_name': GUI_NAME,
            'language': GUI_LANG,
            'theme_name': THEME_NAME,
            'sickrage_background': int(SICKRAGE_BACKGROUND),
            'sickrage_background_path': SICKRAGE_BACKGROUND_PATH,
            'fanart_background': int(FANART_BACKGROUND),
            'fanart_background_opacity': FANART_BACKGROUND_OPACITY,
            'home_layout': HOME_LAYOUT,
            'history_layout': HISTORY_LAYOUT,
            'history_limit': HISTORY_LIMIT,
            'display_show_specials': int(DISPLAY_SHOW_SPECIALS),
            'coming_eps_layout': COMING_EPS_LAYOUT,
            'coming_eps_display_paused': int(COMING_EPS_DISPLAY_PAUSED),
            'coming_eps_sort': COMING_EPS_SORT,
            'coming_eps_missed_range': int(COMING_EPS_MISSED_RANGE),
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
            'addic7ed_username': ADDIC7ED_USER,
            'addic7ed_password': helpers.encrypt(ADDIC7ED_PASS, ENCRYPTION_VERSION),

            'itasa_username': ITASA_USER,
            'itasa_password': helpers.encrypt(ITASA_PASS, ENCRYPTION_VERSION),

            'legendastv_username': LEGENDASTV_USER,
            'legendastv_password': helpers.encrypt(LEGENDASTV_PASS, ENCRYPTION_VERSION),

            'opensubtitles_username': OPENSUBTITLES_USER,
            'opensubtitles_password': helpers.encrypt(OPENSUBTITLES_PASS, ENCRYPTION_VERSION),
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
        }
    })
    new_config.write()


def launchBrowser(protocol='http', startPort=None, web_root='/'):

    try:
        import webbrowser
    except ImportError:
        logger.log(u"Unable to load the webbrowser module, cannot launch the browser.", logger.WARNING)
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
            logger.log(u"Unable to launch a browser", logger.ERROR)
