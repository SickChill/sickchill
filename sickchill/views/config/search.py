import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, filters, helpers, ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/search(/?.*)", name="config:search")
class ConfigSearch(Config):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_search.mako")

        return t.render(
            submenu=self.ConfigMenu(), title=_("Config - Episode Search"), header=_("Search Settings"), topmenu="config", controller="config", action="search"
        )

    def saveSearch(
        self,
        use_nzbs=None,
        use_torrents=None,
        nzb_dir=None,
        sab_username=None,
        sab_password=None,
        sab_apikey=None,
        sab_category=None,
        sab_category_anime=None,
        sab_category_backlog=None,
        sab_category_anime_backlog=None,
        sab_host=None,
        nzbget_username=None,
        nzbget_password=None,
        nzbget_category=None,
        nzbget_category_backlog=None,
        nzbget_category_anime=None,
        nzbget_category_anime_backlog=None,
        nzbget_priority=None,
        nzbget_host=None,
        nzbget_use_https=None,
        backlog_days=None,
        backlog_frequency=None,
        dailysearch_frequency=None,
        nzb_method=None,
        torrent_method=None,
        usenet_retention=None,
        download_propers=None,
        check_propers_interval=None,
        allow_high_priority=None,
        sab_forced=None,
        randomize_providers=None,
        use_failed_downloads=None,
        delete_failed=None,
        backlog_missing_only=None,
        torrent_dir=None,
        torrent_username=None,
        torrent_password=None,
        torrent_host=None,
        torrent_label=None,
        torrent_label_anime=None,
        torrent_path=None,
        torrent_path_incomplete=None,
        torrent_verify_cert=None,
        torrent_seed_time=None,
        torrent_paused=None,
        torrent_high_bandwidth=None,
        torrent_rpcurl=None,
        torrent_auth_type=None,
        ignore_words=None,
        trackers_list=None,
        require_words=None,
        ignored_subs_list=None,
        syno_dsm_host=None,
        syno_dsm_user=None,
        syno_dsm_pass=None,
        syno_dsm_path=None,
        quality_allow_hevc=False,
        prefer_words=None,
    ):

        results = []

        if not config.change_nzb_dir(nzb_dir):
            results += ["Unable to create directory " + os.path.normpath(nzb_dir) + ", dir not changed."]

        if not config.change_torrent_dir(torrent_dir):
            results += ["Unable to create directory " + os.path.normpath(torrent_dir) + ", dir not changed."]

        config.change_daily_search_frequency(dailysearch_frequency)

        config.change_backlog_frequency(backlog_frequency)
        settings.BACKLOG_DAYS = try_int(backlog_days, 7)

        settings.USE_NZBS = config.checkbox_to_value(use_nzbs)
        settings.USE_TORRENTS = config.checkbox_to_value(use_torrents)

        settings.NZB_METHOD = nzb_method
        settings.TORRENT_METHOD = torrent_method
        settings.USENET_RETENTION = try_int(usenet_retention, 500)

        settings.IGNORE_WORDS = ignore_words if ignore_words else ""
        settings.TRACKERS_LIST = trackers_list if trackers_list else ""
        settings.REQUIRE_WORDS = require_words if require_words else ""
        settings.PREFER_WORDS = prefer_words if prefer_words else ""
        settings.IGNORED_SUBS_LIST = ignored_subs_list if ignored_subs_list else ""

        settings.RANDOMIZE_PROVIDERS = config.checkbox_to_value(randomize_providers)

        config.change_download_propers(download_propers)

        settings.CHECK_PROPERS_INTERVAL = check_propers_interval

        settings.ALLOW_HIGH_PRIORITY = config.checkbox_to_value(allow_high_priority)
        settings.QUALITY_ALLOW_HEVC = config.checkbox_to_value(quality_allow_hevc)

        settings.USE_FAILED_DOWNLOADS = config.checkbox_to_value(use_failed_downloads)
        settings.DELETE_FAILED = config.checkbox_to_value(delete_failed)

        settings.BACKLOG_MISSING_ONLY = config.checkbox_to_value(backlog_missing_only)

        settings.SAB_USERNAME = sab_username
        settings.SAB_PASSWORD = filters.unhide(settings.SAB_PASSWORD, sab_password)
        settings.SAB_APIKEY = filters.unhide(settings.SAB_APIKEY, sab_apikey.strip())
        settings.SAB_CATEGORY = sab_category
        settings.SAB_CATEGORY_BACKLOG = sab_category_backlog
        settings.SAB_CATEGORY_ANIME = sab_category_anime
        settings.SAB_CATEGORY_ANIME_BACKLOG = sab_category_anime_backlog
        settings.SAB_HOST = config.clean_url(sab_host)
        settings.SAB_FORCED = config.checkbox_to_value(sab_forced)

        settings.NZBGET_USERNAME = nzbget_username
        settings.NZBGET_PASSWORD = filters.unhide(settings.NZBGET_PASSWORD, nzbget_password)
        settings.NZBGET_CATEGORY = nzbget_category
        settings.NZBGET_CATEGORY_BACKLOG = nzbget_category_backlog
        settings.NZBGET_CATEGORY_ANIME = nzbget_category_anime
        settings.NZBGET_CATEGORY_ANIME_BACKLOG = nzbget_category_anime_backlog
        settings.NZBGET_HOST = config.clean_host(nzbget_host)
        settings.NZBGET_USE_HTTPS = config.checkbox_to_value(nzbget_use_https)
        settings.NZBGET_PRIORITY = try_int(nzbget_priority, 100)

        settings.TORRENT_USERNAME = torrent_username
        settings.TORRENT_PASSWORD = filters.unhide(settings.TORRENT_PASSWORD, torrent_password)
        settings.TORRENT_LABEL = torrent_label
        settings.TORRENT_LABEL_ANIME = torrent_label_anime
        settings.TORRENT_VERIFY_CERT = config.checkbox_to_value(torrent_verify_cert)

        settings.TORRENT_PATH = torrent_path.rstrip("/\\")
        settings.TORRENT_PATH_INCOMPLETE = torrent_path_incomplete.rstrip("/\\")

        settings.TORRENT_SEED_TIME = torrent_seed_time
        settings.TORRENT_PAUSED = config.checkbox_to_value(torrent_paused)
        settings.TORRENT_HIGH_BANDWIDTH = config.checkbox_to_value(torrent_high_bandwidth)
        settings.TORRENT_HOST = config.clean_url(torrent_host)
        settings.TORRENT_RPCURL = torrent_rpcurl
        settings.TORRENT_AUTH_TYPE = torrent_auth_type

        settings.SYNOLOGY_DSM_HOST = config.clean_url(syno_dsm_host)
        settings.SYNOLOGY_DSM_USERNAME = syno_dsm_user
        settings.SYNOLOGY_DSM_PASSWORD = filters.unhide(settings.SYNOLOGY_DSM_PASSWORD, syno_dsm_pass)
        settings.SYNOLOGY_DSM_PATH = syno_dsm_path.rstrip("/\\")

        # This is a PITA, but lets merge the settings if they only set DSM up in one section to save them some time
        if settings.TORRENT_METHOD == "download_station":
            if not settings.SYNOLOGY_DSM_HOST:
                settings.SYNOLOGY_DSM_HOST = settings.TORRENT_HOST
            if not settings.SYNOLOGY_DSM_USERNAME:
                settings.SYNOLOGY_DSM_USERNAME = settings.TORRENT_USERNAME
            if not settings.SYNOLOGY_DSM_PASSWORD:
                settings.SYNOLOGY_DSM_PASSWORD = settings.TORRENT_PASSWORD
            if not settings.SYNOLOGY_DSM_PATH:
                settings.SYNOLOGY_DSM_PATH = settings.TORRENT_PATH

        if settings.NZB_METHOD == "download_station":
            if not settings.TORRENT_HOST:
                settings.TORRENT_HOST = settings.SYNOLOGY_DSM_HOST
            if not settings.TORRENT_USERNAME:
                settings.TORRENT_USERNAME = settings.SYNOLOGY_DSM_USERNAME
            if not settings.TORRENT_PASSWORD:
                settings.TORRENT_PASSWORD = settings.SYNOLOGY_DSM_PASSWORD
            if not settings.TORRENT_PATH:
                settings.TORRENT_PATH = settings.SYNOLOGY_DSM_PATH

        helpers.manage_torrents_url(reset=True)

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/search/")
