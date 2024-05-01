import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, filters, ui
from sickchill.views.common import PageTemplate
from sickchill.views.config.index import Config
from sickchill.views.routes import Route


@Route("/config/notifications(/?.*)", name="config:notifications")
class ConfigNotifications(Config):
    @addslash
    def index(self):
        t = PageTemplate(rh=self, filename="config_notifications.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Notifications"),
            header=_("Notifications"),
            topmenu="config",
            controller="config",
            action="notifications",
        )

    def saveNotifications(self):
        results = []

        settings.USE_KODI = config.checkbox_to_value(self.get_body_argument("use_kodi", default=None))
        settings.KODI_ALWAYS_ON = config.checkbox_to_value(self.get_body_argument("kodi_always_on", default=None))
        settings.KODI_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("kodi_notify_onsnatch", default=None))
        settings.KODI_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("kodi_notify_ondownload", default=None))
        settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("kodi_notify_onsubtitledownload", default=None))
        settings.KODI_UPDATE_LIBRARY = config.checkbox_to_value(self.get_body_argument("kodi_update_library", default=None))
        settings.KODI_UPDATE_FULL = config.checkbox_to_value(self.get_body_argument("kodi_update_full", default=None))
        settings.KODI_UPDATE_ONLYFIRST = config.checkbox_to_value(self.get_body_argument("kodi_update_onlyfirst", default=None))
        settings.KODI_HOST = config.clean_hosts(self.get_body_argument("kodi_host", default=None))
        settings.KODI_USERNAME = self.get_body_argument("kodi_username", default=None)
        settings.KODI_PASSWORD = filters.unhide(settings.KODI_PASSWORD, self.get_body_argument("kodi_password", default=None))

        settings.USE_PLEX_SERVER = config.checkbox_to_value(self.get_body_argument("use_plex_server", default=None))
        settings.PLEX_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("plex_notify_onsnatch", default=None))
        settings.PLEX_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("plex_notify_ondownload", default=None))
        settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("plex_notify_onsubtitledownload", default=None))
        settings.PLEX_UPDATE_LIBRARY = config.checkbox_to_value(self.get_body_argument("plex_update_library", default=None))
        settings.PLEX_CLIENT_HOST = config.clean_hosts(self.get_body_argument("plex_client_host", default=None))
        settings.PLEX_SERVER_HOST = config.clean_hosts(self.get_body_argument("plex_server_host", default=None))
        settings.PLEX_SERVER_TOKEN = config.clean_host(self.get_body_argument("plex_server_token", default=None))
        settings.PLEX_SERVER_USERNAME = self.get_body_argument("plex_server_username", default=None)
        settings.PLEX_SERVER_PASSWORD = filters.unhide(settings.PLEX_SERVER_PASSWORD, self.get_body_argument("plex_server_password", default=None))

        settings.USE_PLEX_CLIENT = config.checkbox_to_value(self.get_body_argument("use_plex_client", default=None))
        settings.PLEX_CLIENT_USERNAME = self.get_body_argument("plex_client_username", default=None)
        settings.PLEX_CLIENT_PASSWORD = filters.unhide(settings.PLEX_CLIENT_PASSWORD, self.get_body_argument("plex_client_password", default=None))
        settings.PLEX_SERVER_HTTPS = config.checkbox_to_value(self.get_body_argument("plex_server_https", default=None))

        settings.USE_EMBY = config.checkbox_to_value(self.get_body_argument("use_emby", default=None))
        settings.EMBY_HOST = config.clean_url(self.get_body_argument("emby_host", default=None))
        settings.EMBY_APIKEY = filters.unhide(settings.EMBY_APIKEY, self.get_body_argument("emby_apikey", default=None))

        settings.USE_JELLYFIN = config.checkbox_to_value(self.get_body_argument("use_jellyfin", default=None))
        settings.JELLYFIN_HOST = config.clean_url(self.get_body_argument("jellyfin_host", default=None))
        settings.JELLYFIN_APIKEY = filters.unhide(settings.JELLYFIN_APIKEY, self.get_body_argument("jellyfin_apikey", default=None))

        settings.USE_GROWL = config.checkbox_to_value(self.get_body_argument("use_growl", default=None))
        settings.GROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("growl_notify_onsnatch", default=None))
        settings.GROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("growl_notify_ondownload", default=None))
        settings.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("growl_notify_onsubtitledownload", default=None))
        settings.GROWL_HOST = config.clean_host(self.get_body_argument("growl_host", default=None), default_port=23053)
        settings.GROWL_PASSWORD = filters.unhide(settings.GROWL_PASSWORD, self.get_body_argument("growl_password", default=None))

        settings.USE_FREEMOBILE = config.checkbox_to_value(self.get_body_argument("use_freemobile", default=None))
        settings.FREEMOBILE_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("freemobile_notify_onsnatch", default=None))
        settings.FREEMOBILE_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("freemobile_notify_ondownload", default=None))
        settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("freemobile_notify_onsubtitledownload", default=None))
        settings.FREEMOBILE_ID = self.get_body_argument("freemobile_id", default=None)
        settings.FREEMOBILE_APIKEY = filters.unhide(settings.FREEMOBILE_APIKEY, self.get_body_argument("freemobile_apikey", default=None))

        settings.USE_TELEGRAM = config.checkbox_to_value(self.get_body_argument("use_telegram", default=None))
        settings.TELEGRAM_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("telegram_notify_onsnatch", default=None))
        settings.TELEGRAM_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("telegram_notify_ondownload", default=None))
        settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("telegram_notify_onsubtitledownload", default=None))
        settings.TELEGRAM_ID = self.get_body_argument("telegram_id", default=None)
        settings.TELEGRAM_APIKEY = filters.unhide(settings.TELEGRAM_APIKEY, self.get_body_argument("telegram_apikey", default=None))

        settings.USE_JOIN = config.checkbox_to_value(self.get_body_argument("use_join", default=None))
        settings.JOIN_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("join_notify_onsnatch", default=None))
        settings.JOIN_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("join_notify_ondownload", default=None))
        settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("join_notify_onsubtitledownload", default=None))
        settings.JOIN_ID = self.get_body_argument("join_id", default=None)
        settings.JOIN_APIKEY = filters.unhide(settings.JOIN_APIKEY, self.get_body_argument("join_apikey", default=None))

        settings.USE_PROWL = config.checkbox_to_value(self.get_body_argument("use_prowl", default=None))
        settings.PROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("prowl_notify_onsnatch", default=None))
        settings.PROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("prowl_notify_ondownload", default=None))
        settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("prowl_notify_onsubtitledownload", default=None))
        settings.PROWL_API = self.get_body_argument("prowl_api", default=None)
        settings.PROWL_PRIORITY = self.get_body_argument("prowl_priority", default="0")
        settings.PROWL_MESSAGE_TITLE = self.get_body_argument("prowl_message_title", default=None)

        settings.USE_TWITTER = config.checkbox_to_value(self.get_body_argument("use_twitter", default=None))
        settings.TWITTER_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("twitter_notify_onsnatch", default=None))
        settings.TWITTER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("twitter_notify_ondownload", default=None))
        settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("twitter_notify_onsubtitledownload", default=None))
        settings.TWITTER_USEDM = config.checkbox_to_value(self.get_body_argument("twitter_usedm", default=None))
        settings.TWITTER_DMTO = self.get_body_argument("twitter_dmto", default=None)

        settings.USE_TWILIO = config.checkbox_to_value(self.get_body_argument("use_twilio", default=None))
        settings.TWILIO_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("twilio_notify_onsnatch", default=None))
        settings.TWILIO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("twilio_notify_ondownload", default=None))
        settings.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("twilio_notify_onsubtitledownload", default=None))
        settings.TWILIO_PHONE_SID = self.get_body_argument("twilio_phone_sid", default=None)
        settings.TWILIO_ACCOUNT_SID = self.get_body_argument("twilio_account_sid", default=None)
        settings.TWILIO_AUTH_TOKEN = self.get_body_argument("twilio_auth_token", default=None)
        settings.TWILIO_TO_NUMBER = self.get_body_argument("twilio_to_number", default=None)

        settings.USE_SLACK = config.checkbox_to_value(self.get_body_argument("use_slack", default="False"))
        settings.SLACK_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("slack_notify_snatch", default=None))
        settings.SLACK_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("slack_notify_download", default=None))
        settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("slack_notify_subtitledownload", default=None))
        settings.SLACK_WEBHOOK = self.get_body_argument("slack_webhook", default=None)
        settings.SLACK_ICON_EMOJI = self.get_body_argument("slack_icon_emoji", default=None)

        settings.USE_MATTERMOST = config.checkbox_to_value(self.get_body_argument("trakt_remove_serieslist", default=None))
        settings.MATTERMOST_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("mattermost_notify_snatch", default=None))
        settings.MATTERMOST_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("mattermost_notify_download", default=None))
        settings.MATTERMOST_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("mattermost_notify_subtitledownload", default=None))
        settings.MATTERMOST_WEBHOOK = self.get_body_argument("mattermost_webhook", default=None)
        settings.MATTERMOST_USERNAME = self.get_body_argument("mattermost_username", default=None)
        settings.MATTERMOST_ICON_EMOJI = self.get_body_argument("mattermost_icon_emoji", default=None)

        settings.USE_MATTERMOSTBOT = config.checkbox_to_value(self.get_body_argument("nmjv2_database", default=None))
        settings.MATTERMOSTBOT_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("mattermostbot_notify_snatch", default=None))
        settings.MATTERMOSTBOT_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("mattermostbot_notify_download", default=None))
        settings.MATTERMOSTBOT_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("mattermostbot_notify_subtitledownload", default=None))
        settings.MATTERMOSTBOT_URL = self.get_body_argument("mattermostbot_url", default=None)
        settings.MATTERMOSTBOT_AUTHOR = self.get_body_argument("mattermostbot_author", default=None)
        settings.MATTERMOSTBOT_TOKEN = self.get_body_argument("mattermostbot_token", default=None)
        settings.MATTERMOSTBOT_CHANNEL = self.get_body_argument("mattermostbot_channel", default=None)
        settings.MATTERMOSTBOT_ICON_EMOJI = self.get_body_argument("mattermostbot_icon_emoji", default=None)

        settings.USE_ROCKETCHAT = config.checkbox_to_value(self.get_body_argument("use_rocketchat", default="False"))
        settings.ROCKETCHAT_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("rocketchat_notify_snatch", default=None))
        settings.ROCKETCHAT_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("rocketchat_notify_download", default=None))
        settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("rocketchat_notify_subtitledownload", default=None))
        settings.ROCKETCHAT_WEBHOOK = self.get_body_argument("rocketchat_webhook", default=None)
        settings.ROCKETCHAT_ICON_EMOJI = self.get_body_argument("rocketchat_icon_emoji", default=None)

        settings.USE_MATRIX = config.checkbox_to_value(self.get_body_argument("use_matrix", default="False"))
        settings.MATRIX_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("matrix_notify_snatch", default=None))
        settings.MATRIX_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("matrix_notify_download", default=None))
        settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("matrix_notify_subtitledownload", default=None))
        settings.MATRIX_API_TOKEN = self.get_body_argument("matrix_api_token", default=None)
        settings.MATRIX_SERVER = self.get_body_argument("matrix_server", default=None)
        settings.MATRIX_ROOM = self.get_body_argument("matrix_room", default=None)

        settings.USE_DISCORD = config.checkbox_to_value(self.get_body_argument("use_discord", default="False"))
        settings.DISCORD_NOTIFY_SNATCH = config.checkbox_to_value(self.get_body_argument("discord_notify_snatch", default=None))
        settings.DISCORD_NOTIFY_DOWNLOAD = config.checkbox_to_value(self.get_body_argument("discord_notify_download", default=None))
        settings.DISCORD_WEBHOOK = self.get_body_argument("discord_webhook", default=None)
        settings.DISCORD_NAME = self.get_body_argument("discord_name", default=None)
        settings.DISCORD_AVATAR_URL = self.get_body_argument("discord_avatar_url", default=None)
        settings.DISCORD_TTS = config.checkbox_to_value(self.get_body_argument("discord_tts", default=None))

        settings.USE_BOXCAR2 = config.checkbox_to_value(self.get_body_argument("use_boxcar2", default=None))
        settings.BOXCAR2_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("boxcar2_notify_onsnatch", default=None))
        settings.BOXCAR2_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("boxcar2_notify_ondownload", default=None))
        settings.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("boxcar2_notify_onsubtitledownload", default=None))
        settings.BOXCAR2_ACCESSTOKEN = self.get_body_argument("boxcar2_accesstoken", default=None)

        settings.USE_PUSHOVER = config.checkbox_to_value(self.get_body_argument("use_pushover", default=None))
        settings.PUSHOVER_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("pushover_notify_onsnatch", default=None))
        settings.PUSHOVER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushover_notify_ondownload", default=None))
        settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushover_notify_onsubtitledownload", default=None))
        settings.PUSHOVER_USERKEY = self.get_body_argument("pushover_userkey", default=None)
        settings.PUSHOVER_APIKEY = filters.unhide(settings.PUSHOVER_APIKEY, self.get_body_argument("pushover_apikey", default=None))
        settings.PUSHOVER_DEVICE = self.get_body_argument("pushover_device", default=None)
        settings.PUSHOVER_SOUND = self.get_body_argument("pushover_sound", default=None)
        settings.PUSHOVER_PRIORITY = self.get_body_argument("pushover_priority", default="0")

        settings.USE_LIBNOTIFY = config.checkbox_to_value(self.get_body_argument("use_libnotify", default=None))
        settings.LIBNOTIFY_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("libnotify_notify_onsnatch", default=None))
        settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("libnotify_notify_ondownload", default=None))
        settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("libnotify_notify_onsubtitledownload", default=None))

        settings.USE_NMJ = config.checkbox_to_value(self.get_body_argument("use_nmj", default=None))
        settings.NMJ_HOST = config.clean_host(self.get_body_argument("nmj_host", default=None))
        settings.NMJ_DATABASE = self.get_body_argument("nmj_database", default=None)
        settings.NMJ_MOUNT = self.get_body_argument("nmj_mount", default=None)

        settings.USE_NMJv2 = config.checkbox_to_value(self.get_body_argument("use_nmjv2", default=None))
        settings.NMJv2_HOST = config.clean_host(self.get_body_argument("nmjv2_host", default=None))
        settings.NMJv2_DATABASE = self.get_body_argument("nmjv2_database", default=None)
        settings.NMJv2_DBLOC = self.get_body_argument("nmjv2_dbloc", default=None)

        settings.USE_SYNOINDEX = config.checkbox_to_value(self.get_body_argument("use_synoindex", default=None))

        settings.USE_SYNOLOGYNOTIFIER = config.checkbox_to_value(self.get_body_argument("use_synologynotifier", default=None))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("synologynotifier_notify_onsnatch", default=None))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("synologynotifier_notify_ondownload", default=None))
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(
            self.get_body_argument("synologynotifier_notify_onsubtitledownload", default=None)
        )

        config.change_use_trakt(self.get_body_argument("use_trakt", default=None))
        settings.TRAKT_USERNAME = self.get_body_argument("trakt_username", default=None)
        settings.TRAKT_REMOVE_WATCHLIST = config.checkbox_to_value(self.get_body_argument("trakt_remove_watchlist", default=None))
        settings.TRAKT_REMOVE_SERIESLIST = config.checkbox_to_value(self.get_body_argument("trakt_remove_serieslist", default=None))
        settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL = config.checkbox_to_value(self.get_body_argument("trakt_remove_show_from_sickchill", default=None))
        settings.TRAKT_SYNC_WATCHLIST = config.checkbox_to_value(self.get_body_argument("trakt_sync_watchlist", default=None))
        settings.TRAKT_METHOD_ADD = int(self.get_body_argument("trakt_method_add", default=None))
        settings.TRAKT_START_PAUSED = config.checkbox_to_value(self.get_body_argument("trakt_start_paused", default=None))
        settings.TRAKT_USE_RECOMMENDED = config.checkbox_to_value(self.get_body_argument("trakt_use_recommended", default=None))
        settings.TRAKT_SYNC = config.checkbox_to_value(self.get_body_argument("trakt_sync", default=None))
        settings.TRAKT_SYNC_REMOVE = config.checkbox_to_value(self.get_body_argument("trakt_sync_remove", default=None))
        settings.TRAKT_DEFAULT_INDEXER = int(self.get_body_argument("trakt_default_indexer", default=None))
        settings.TRAKT_TIMEOUT = int(self.get_body_argument("trakt_timeout", default=None))
        settings.TRAKT_BLACKLIST_NAME = self.get_body_argument("trakt_blacklist_name", default=None)

        settings.USE_EMAIL = config.checkbox_to_value(self.get_body_argument("use_email", default=None))
        settings.EMAIL_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("email_notify_onsnatch", default=None))
        settings.EMAIL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("email_notify_ondownload", default=None))
        settings.EMAIL_NOTIFY_ONPOSTPROCESS = config.checkbox_to_value(self.get_body_argument("email_notify_onpostprocess", default=None))
        settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("email_notify_onsubtitledownload", default=None))
        settings.EMAIL_HOST = config.clean_host(self.get_body_argument("email_host", default=None))
        settings.EMAIL_PORT = try_int(self.get_body_argument("email_port", default="25"))
        settings.EMAIL_FROM = self.get_body_argument("email_from", default=None)
        settings.EMAIL_TLS = config.checkbox_to_value(self.get_body_argument("email_tls", default=None))
        settings.EMAIL_USER = self.get_body_argument("email_user", default=None)
        settings.EMAIL_PASSWORD = filters.unhide(settings.EMAIL_PASSWORD, self.get_body_argument("email_password", default=None))
        settings.EMAIL_LIST = self.get_body_argument("email_list", default=None)
        settings.EMAIL_SUBJECT = self.get_body_argument("email_subject", default=None)

        settings.USE_PYTIVO = config.checkbox_to_value(self.get_body_argument("use_pytivo", default=None))
        settings.PYTIVO_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("pytivo_notify_onsnatch", default=None))
        settings.PYTIVO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pytivo_notify_ondownload", default=None))
        settings.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pytivo_notify_onsubtitledownload", default=None))
        settings.PYTIVO_UPDATE_LIBRARY = config.checkbox_to_value(self.get_body_argument("pytivo_update_library", default=None))
        settings.PYTIVO_HOST = config.clean_host(self.get_body_argument("pytivo_host", default=None))
        settings.PYTIVO_SHARE_NAME = self.get_body_argument("pytivo_share_name", default=None)
        settings.PYTIVO_TIVO_NAME = self.get_body_argument("pytivo_tivo_name", default=None)

        settings.USE_PUSHALOT = config.checkbox_to_value(self.get_body_argument("use_pushalot", default=None))
        settings.PUSHALOT_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("pushalot_notify_onsnatch", default=None))
        settings.PUSHALOT_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushalot_notify_ondownload", default=None))
        settings.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushalot_notify_onsubtitledownload", default=None))
        settings.PUSHALOT_AUTHORIZATIONTOKEN = self.get_body_argument("pushalot_authorizationtoken", default=None)

        settings.USE_PUSHBULLET = config.checkbox_to_value(self.get_body_argument("use_pushbullet", default=None))
        settings.PUSHBULLET_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("pushbullet_notify_onsnatch", default=None))
        settings.PUSHBULLET_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushbullet_notify_ondownload", default=None))
        settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("pushbullet_notify_onsubtitledownload", default=None))
        settings.PUSHBULLET_API = self.get_body_argument("pushbullet_api", default=None)
        settings.PUSHBULLET_DEVICE = self.get_body_argument("pushbullet_device_list", default=None)
        settings.PUSHBULLET_CHANNEL = self.get_body_argument("pushbullet_channel_list", default="")

        settings.USE_GOTIFY = config.checkbox_to_value(self.get_body_argument("use_gotify", default=None))
        settings.GOTIFY_NOTIFY_ONSNATCH = config.checkbox_to_value(self.get_body_argument("gotify_notify_onsnatch", default=None))
        settings.GOTIFY_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(self.get_body_argument("gotify_notify_ondownload", default=None))
        settings.GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(self.get_body_argument("gotify_notify_onsubtitledownload", default=None))
        settings.GOTIFY_HOST = self.get_body_argument("gotify_host", default=None)
        settings.GOTIFY_AUTHORIZATIONTOKEN = self.get_body_argument("gotify_authorizationtoken", default=None)

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/notifications/")
