import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, filters, helpers, ui
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/search(/?.*)", name="config:search")
class ConfigSearch(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_search.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Episode Search"),
            header=_("Search Settings"),
            topmenu="config",
            controller="config",
            action="search",
        )

    def saveSearch(self):
        nzb_dir = self.get_body_argument("nzb_dir", default=None)
        torrent_dir = self.get_body_argument("torrent_dir", default=None)
        results = []

        if not config.change_nzb_dir(nzb_dir):
            results += ["Unable to create directory " + os.path.normpath(nzb_dir) + ", dir not changed."]

        if not config.change_torrent_dir(torrent_dir):
            results += ["Unable to create directory " + os.path.normpath(torrent_dir) + ", dir not changed."]

        config.change_daily_search_frequency(self.get_body_argument("dailysearch_frequency", default=None))

        config.change_backlog_frequency(self.get_body_argument("backlog_frequency", default=None))
        settings.BACKLOG_DAYS = try_int(self.get_body_argument("backlog_days", default="7"))

        settings.USE_NZBS = config.checkbox_to_value(self.get_body_argument("use_nzbs", default=None))
        settings.USE_TORRENTS = config.checkbox_to_value(self.get_body_argument("use_torrents", default=None))

        settings.NZB_METHOD = self.get_body_argument("nzb_method", default=None)
        settings.TORRENT_METHOD = self.get_body_argument("torrent_method", default=None)
        settings.USENET_RETENTION = try_int(self.get_body_argument("usenet_retention", default="500"))
        settings.CACHE_RETENTION = try_int(self.get_body_argument("cache_retention", default="30"))
        settings.SHOW_SKIP_OLDER = try_int(self.get_body_argument("show_skip_older", default="30"))

        settings.IGNORE_WORDS = self.get_body_argument("ignore_words", default="")
        settings.TRACKERS_LIST = self.get_body_argument("trackers_list", default="")
        settings.REQUIRE_WORDS = self.get_body_argument("require_words", default="")
        settings.PREFER_WORDS = self.get_body_argument("prefer_words", default="")
        settings.IGNORED_SUBS_LIST = self.get_body_argument("ignored_subs_list", default="")

        settings.RANDOMIZE_PROVIDERS = config.checkbox_to_value(self.get_body_argument("randomize_providers", default=None))

        config.change_download_propers(self.get_body_argument("download_propers", default=None))

        settings.CHECK_PROPERS_INTERVAL = self.get_body_argument("check_propers_interval", default=None)

        settings.ALLOW_HIGH_PRIORITY = config.checkbox_to_value(self.get_body_argument("allow_high_priority", default=None))

        settings.USE_FAILED_DOWNLOADS = config.checkbox_to_value(self.get_body_argument("use_failed_downloads", default=None))
        settings.DELETE_FAILED = config.checkbox_to_value(self.get_body_argument("delete_failed", default=None))

        settings.BACKLOG_MISSING_ONLY = config.checkbox_to_value(self.get_body_argument("backlog_missing_only", default=None))

        settings.SAB_USERNAME = self.get_body_argument("sab_username", default=None)
        settings.SAB_PASSWORD = filters.unhide(settings.SAB_PASSWORD, self.get_body_argument("sab_password", default=None))
        settings.SAB_APIKEY = filters.unhide(settings.SAB_APIKEY, self.get_body_argument("sab_apikey", default=None).strip())
        settings.SAB_CATEGORY = self.get_body_argument("sab_category", default=None)
        settings.SAB_CATEGORY_BACKLOG = self.get_body_argument("sab_category_backlog", default=None)
        settings.SAB_CATEGORY_ANIME = self.get_body_argument("sab_category_anime", default=None)
        settings.SAB_CATEGORY_ANIME_BACKLOG = self.get_body_argument("sab_category_anime_backlog", default=None)
        settings.SAB_HOST = config.clean_url(self.get_body_argument("sab_host", default=None))
        settings.SAB_FORCED = config.checkbox_to_value(self.get_body_argument("sab_forced", default=None))

        settings.NZBGET_USERNAME = self.get_body_argument("nzbget_username", default=None)
        settings.NZBGET_PASSWORD = filters.unhide(settings.NZBGET_PASSWORD, self.get_body_argument("nzbget_password", default=None))
        settings.NZBGET_CATEGORY = self.get_body_argument("nzbget_category", default=None)
        settings.NZBGET_CATEGORY_BACKLOG = self.get_body_argument("nzbget_category_backlog", default=None)
        settings.NZBGET_CATEGORY_ANIME = self.get_body_argument("nzbget_category_anime", default=None)
        settings.NZBGET_CATEGORY_ANIME_BACKLOG = self.get_body_argument("nzbget_category_anime_backlog", default=None)
        settings.NZBGET_HOST = config.clean_host(self.get_body_argument("nzbget_host", default=None))
        settings.NZBGET_USE_HTTPS = config.checkbox_to_value(self.get_body_argument("nzbget_use_https", default=None))
        settings.NZBGET_PRIORITY = try_int(self.get_body_argument("nzbget_priority", default="100"))

        settings.TORRENT_USERNAME = self.get_body_argument("torrent_username", default=None)
        settings.TORRENT_PASSWORD = filters.unhide(settings.TORRENT_PASSWORD, self.get_body_argument("torrent_password", default=None))
        settings.TORRENT_LABEL = self.get_body_argument("torrent_label", default=None)
        settings.TORRENT_LABEL_ANIME = self.get_body_argument("torrent_label_anime", default=None)
        settings.TORRENT_VERIFY_CERT = config.checkbox_to_value(self.get_body_argument("torrent_verify_cert", default=None))

        settings.TORRENT_PATH = self.get_body_argument("torrent_path", default=None).rstrip("/\\")
        settings.TORRENT_PATH_INCOMPLETE = self.get_body_argument("torrent_path_incomplete", default=None).rstrip("/\\")

        settings.TORRENT_SEED_TIME = self.get_body_argument("torrent_seed_time", default=None)
        settings.TORRENT_PAUSED = config.checkbox_to_value(self.get_body_argument("torrent_paused", default=None))
        settings.TORRENT_HIGH_BANDWIDTH = config.checkbox_to_value(self.get_body_argument("torrent_high_bandwidth", default=None))
        settings.TORRENT_HOST = config.clean_url(self.get_body_argument("torrent_host", default=None))
        settings.TORRENT_RPCURL = self.get_body_argument("torrent_rpcurl", default=None)
        settings.TORRENT_AUTH_TYPE = self.get_body_argument("torrent_auth_type", default=None)

        settings.SYNOLOGY_DSM_HOST = config.clean_url(self.get_body_argument("syno_dsm_host", default=None))
        settings.SYNOLOGY_DSM_USERNAME = self.get_body_argument("syno_dsm_user", default=None)
        settings.SYNOLOGY_DSM_PASSWORD = filters.unhide(settings.SYNOLOGY_DSM_PASSWORD, self.get_body_argument("syno_dsm_pass", default=None))
        settings.SYNOLOGY_DSM_PATH = self.get_body_argument("syno_dsm_path", default=None).rstrip("/\\")

        settings.FLARESOLVERR_URI = config.clean_url(self.get_body_argument("flaresolverr_uri", default=None))

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
