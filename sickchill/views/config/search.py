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
# pylint: disable=abstract-method,too-many-lines, R

from __future__ import absolute_import, print_function, unicode_literals

import os

from tornado.web import addslash

import sickbeard
from sickbeard import config, filters, helpers, logger, ui
from sickchill.helper import try_int
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config

try:
    import json
except ImportError:
    # noinspection PyPackageRequirements,PyUnresolvedReferences
    import simplejson as json


@Route('/config/search(/?.*)', name='config:search')
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigSearch, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_search.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Episode Search'),
                        header=_('Search Settings'), topmenu='config',
                        controller="config", action="search")

    def saveSearch(self, use_nzbs=None, use_torrents=None, nzb_dir=None, sab_username=None, sab_password=None,
                   sab_apikey=None, sab_category=None, sab_category_anime=None, sab_category_backlog=None, sab_category_anime_backlog=None, sab_host=None,
                   nzbget_username=None, nzbget_password=None, nzbget_category=None, nzbget_category_backlog=None, nzbget_category_anime=None,
                   nzbget_category_anime_backlog=None, nzbget_priority=None, nzbget_host=None, nzbget_use_https=None,
                   backlog_days=None, backlog_frequency=None, dailysearch_frequency=None, nzb_method=None, torrent_method=None, usenet_retention=None,
                   download_propers=None, check_propers_interval=None, allow_high_priority=None, sab_forced=None,
                   randomize_providers=None, use_failed_downloads=None, delete_failed=None,
                   torrent_dir=None, torrent_username=None, torrent_password=None, torrent_host=None,
                   torrent_label=None, torrent_label_anime=None, torrent_path=None, torrent_download_dir_deluge=None,
                   torrent_complete_dir_deluge=None, torrent_verify_cert=None,
                   torrent_seed_time=None, torrent_paused=None, torrent_high_bandwidth=None,
                   torrent_rpcurl=None, torrent_auth_type=None, ignore_words=None, trackers_list=None, require_words=None, ignored_subs_list=None,
                   syno_dsm_host=None, syno_dsm_user=None, syno_dsm_pass=None, syno_dsm_path=None, quality_allow_hevc=False, prefer_words=None):

        results = []

        if not config.change_nzb_dir(nzb_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, nzb_dir) + ", dir not changed."]

        if not config.change_torrent_dir(torrent_dir):
            results += ["Unable to create directory " + ek(os.path.normpath, torrent_dir) + ", dir not changed."]

        config.change_daily_search_frequency(dailysearch_frequency)

        config.change_backlog_frequency(backlog_frequency)
        sickbeard.BACKLOG_DAYS = try_int(backlog_days, 7)

        sickbeard.USE_NZBS = config.checkbox_to_value(use_nzbs)
        sickbeard.USE_TORRENTS = config.checkbox_to_value(use_torrents)

        sickbeard.NZB_METHOD = nzb_method
        sickbeard.TORRENT_METHOD = torrent_method
        sickbeard.USENET_RETENTION = try_int(usenet_retention, 500)

        sickbeard.IGNORE_WORDS = ignore_words if ignore_words else ""
        sickbeard.TRACKERS_LIST = trackers_list if trackers_list else ""
        sickbeard.REQUIRE_WORDS = require_words if require_words else ""
        sickbeard.PREFER_WORDS = prefer_words if prefer_words else ""
        sickbeard.IGNORED_SUBS_LIST = ignored_subs_list if ignored_subs_list else ""

        sickbeard.RANDOMIZE_PROVIDERS = config.checkbox_to_value(randomize_providers)

        config.change_download_propers(download_propers)

        sickbeard.CHECK_PROPERS_INTERVAL = check_propers_interval

        sickbeard.ALLOW_HIGH_PRIORITY = config.checkbox_to_value(allow_high_priority)
        sickbeard.QUALITY_ALLOW_HEVC = config.checkbox_to_value(quality_allow_hevc)

        sickbeard.USE_FAILED_DOWNLOADS = config.checkbox_to_value(use_failed_downloads)
        sickbeard.DELETE_FAILED = config.checkbox_to_value(delete_failed)

        sickbeard.SAB_USERNAME = sab_username
        sickbeard.SAB_PASSWORD = filters.unhide(sickbeard.SAB_PASSWORD, sab_password)
        sickbeard.SAB_APIKEY = filters.unhide(sickbeard.SAB_APIKEY, sab_apikey.strip())
        sickbeard.SAB_CATEGORY = sab_category
        sickbeard.SAB_CATEGORY_BACKLOG = sab_category_backlog
        sickbeard.SAB_CATEGORY_ANIME = sab_category_anime
        sickbeard.SAB_CATEGORY_ANIME_BACKLOG = sab_category_anime_backlog
        sickbeard.SAB_HOST = config.clean_url(sab_host)
        sickbeard.SAB_FORCED = config.checkbox_to_value(sab_forced)

        sickbeard.NZBGET_USERNAME = nzbget_username
        sickbeard.NZBGET_PASSWORD = filters.unhide(sickbeard.NZBGET_PASSWORD, nzbget_password)
        sickbeard.NZBGET_CATEGORY = nzbget_category
        sickbeard.NZBGET_CATEGORY_BACKLOG = nzbget_category_backlog
        sickbeard.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        sickbeard.NZBGET_CATEGORY_ANIME_BACKLOG = nzbget_category_anime_backlog
        sickbeard.NZBGET_HOST = config.clean_host(nzbget_host)
        sickbeard.NZBGET_USE_HTTPS = config.checkbox_to_value(nzbget_use_https)
        sickbeard.NZBGET_PRIORITY = try_int(nzbget_priority, 100)

        sickbeard.TORRENT_USERNAME = torrent_username
        sickbeard.TORRENT_PASSWORD = filters.unhide(sickbeard.TORRENT_PASSWORD, torrent_password)
        sickbeard.TORRENT_LABEL = torrent_label
        sickbeard.TORRENT_LABEL_ANIME = torrent_label_anime
        sickbeard.TORRENT_VERIFY_CERT = config.checkbox_to_value(torrent_verify_cert)

        sickbeard.TORRENT_PATH = torrent_path.rstrip('/\\')
        sickbeard.TORRENT_DELUGE_DOWNLOAD_DIR = torrent_download_dir_deluge.rstrip('/\\')
        sickbeard.TORRENT_DELUGE_COMPLETE_DIR = torrent_complete_dir_deluge.rstrip('/\\')

        sickbeard.TORRENT_SEED_TIME = torrent_seed_time
        sickbeard.TORRENT_PAUSED = config.checkbox_to_value(torrent_paused)
        sickbeard.TORRENT_HIGH_BANDWIDTH = config.checkbox_to_value(torrent_high_bandwidth)
        sickbeard.TORRENT_HOST = config.clean_url(torrent_host)
        sickbeard.TORRENT_RPCURL = torrent_rpcurl
        sickbeard.TORRENT_AUTH_TYPE = torrent_auth_type

        sickbeard.SYNOLOGY_DSM_HOST = config.clean_url(syno_dsm_host)
        sickbeard.SYNOLOGY_DSM_USERNAME = syno_dsm_user
        sickbeard.SYNOLOGY_DSM_PASSWORD = filters.unhide(sickbeard.SYNOLOGY_DSM_PASSWORD, syno_dsm_pass)
        sickbeard.SYNOLOGY_DSM_PATH = syno_dsm_path.rstrip('/\\')

        # This is a PITA, but lets merge the settings if they only set DSM up in one section to save them some time
        if sickbeard.TORRENT_METHOD == 'download_station':
            if not sickbeard.SYNOLOGY_DSM_HOST:
                sickbeard.SYNOLOGY_DSM_HOST = sickbeard.TORRENT_HOST
            if not sickbeard.SYNOLOGY_DSM_USERNAME:
                sickbeard.SYNOLOGY_DSM_USERNAME = sickbeard.TORRENT_USERNAME
            if not sickbeard.SYNOLOGY_DSM_PASSWORD:
                sickbeard.SYNOLOGY_DSM_PASSWORD = sickbeard.TORRENT_PASSWORD
            if not sickbeard.SYNOLOGY_DSM_PATH:
                sickbeard.SYNOLOGY_DSM_PATH = sickbeard.TORRENT_PATH

        if sickbeard.NZB_METHOD == 'download_station':
            if not sickbeard.TORRENT_HOST:
                sickbeard.TORRENT_HOST = sickbeard.SYNOLOGY_DSM_HOST
            if not sickbeard.TORRENT_USERNAME:
                sickbeard.TORRENT_USERNAME = sickbeard.SYNOLOGY_DSM_USERNAME
            if not sickbeard.TORRENT_PASSWORD:
                sickbeard.TORRENT_PASSWORD = sickbeard.SYNOLOGY_DSM_PASSWORD
            if not sickbeard.TORRENT_PATH:
                sickbeard.TORRENT_PATH = sickbeard.SYNOLOGY_DSM_PATH

        helpers.manage_torrents_url(reset=True)

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/search/")
