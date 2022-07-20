import os

from tornado.web import addslash

import sickchill.start
from sickchill import logger, settings
from sickchill.helper import try_int
from sickchill.oldbeard import config, filters, ui
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

from . import Config


@Route("/config/notifications(/?.*)", name="config:notifications")
class ConfigNotifications(Config):
    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_notifications.mako")

        return t.render(
            submenu=self.ConfigMenu(),
            title=_("Config - Notifications"),
            header=_("Notifications"),
            topmenu="config",
            controller="config",
            action="notifications",
        )

    def saveNotifications(
        self,
        use_kodi=None,
        kodi_always_on=None,
        kodi_notify_onsnatch=None,
        kodi_notify_ondownload=None,
        kodi_notify_onsubtitledownload=None,
        kodi_update_onlyfirst=None,
        kodi_update_library=None,
        kodi_update_full=None,
        kodi_host=None,
        kodi_username=None,
        kodi_password=None,
        use_plex_server=None,
        plex_notify_onsnatch=None,
        plex_notify_ondownload=None,
        plex_notify_onsubtitledownload=None,
        plex_update_library=None,
        plex_server_host=None,
        plex_server_token=None,
        plex_client_host=None,
        plex_server_username=None,
        plex_server_password=None,
        use_plex_client=None,
        plex_client_username=None,
        plex_client_password=None,
        plex_server_https=None,
        use_emby=None,
        emby_host=None,
        emby_apikey=None,
        use_growl=None,
        growl_notify_onsnatch=None,
        growl_notify_ondownload=None,
        growl_notify_onsubtitledownload=None,
        growl_host=None,
        growl_password=None,
        use_freemobile=None,
        freemobile_notify_onsnatch=None,
        freemobile_notify_ondownload=None,
        freemobile_notify_onsubtitledownload=None,
        freemobile_id=None,
        freemobile_apikey=None,
        use_telegram=None,
        telegram_notify_onsnatch=None,
        telegram_notify_ondownload=None,
        telegram_notify_onsubtitledownload=None,
        telegram_id=None,
        telegram_apikey=None,
        use_join=None,
        join_notify_onsnatch=None,
        join_notify_ondownload=None,
        join_notify_onsubtitledownload=None,
        join_id=None,
        join_apikey=None,
        use_prowl=None,
        prowl_notify_onsnatch=None,
        prowl_notify_ondownload=None,
        prowl_notify_onsubtitledownload=None,
        prowl_api=None,
        prowl_priority=0,
        prowl_show_list=None,
        prowl_show=None,
        prowl_message_title=None,
        use_twitter=None,
        twitter_notify_onsnatch=None,
        twitter_notify_ondownload=None,
        twitter_notify_onsubtitledownload=None,
        twitter_usedm=None,
        twitter_dmto=None,
        use_twilio=None,
        twilio_notify_onsnatch=None,
        twilio_notify_ondownload=None,
        twilio_notify_onsubtitledownload=None,
        twilio_phone_sid=None,
        twilio_account_sid=None,
        twilio_auth_token=None,
        twilio_to_number=None,
        use_boxcar2=None,
        boxcar2_notify_onsnatch=None,
        boxcar2_notify_ondownload=None,
        boxcar2_notify_onsubtitledownload=None,
        boxcar2_accesstoken=None,
        use_pushover=None,
        pushover_notify_onsnatch=None,
        pushover_notify_ondownload=None,
        pushover_notify_onsubtitledownload=None,
        pushover_userkey=None,
        pushover_apikey=None,
        pushover_device=None,
        pushover_sound=None,
        pushover_priority=0,
        use_libnotify=None,
        libnotify_notify_onsnatch=None,
        libnotify_notify_ondownload=None,
        libnotify_notify_onsubtitledownload=None,
        use_nmj=None,
        nmj_host=None,
        nmj_database=None,
        nmj_mount=None,
        use_synoindex=None,
        use_nmjv2=None,
        nmjv2_host=None,
        nmjv2_dbloc=None,
        nmjv2_database=None,
        use_trakt=None,
        trakt_username=None,
        trakt_pin=None,
        trakt_remove_watchlist=None,
        trakt_sync_watchlist=None,
        trakt_remove_show_from_sickchill=None,
        trakt_method_add=None,
        trakt_start_paused=None,
        trakt_use_recommended=None,
        trakt_sync=None,
        trakt_sync_remove=None,
        trakt_default_indexer=None,
        trakt_remove_serieslist=None,
        trakt_timeout=None,
        trakt_blacklist_name=None,
        use_synologynotifier=None,
        synologynotifier_notify_onsnatch=None,
        synologynotifier_notify_ondownload=None,
        synologynotifier_notify_onsubtitledownload=None,
        use_pytivo=None,
        pytivo_notify_onsnatch=None,
        pytivo_notify_ondownload=None,
        pytivo_notify_onsubtitledownload=None,
        pytivo_update_library=None,
        pytivo_host=None,
        pytivo_share_name=None,
        pytivo_tivo_name=None,
        use_pushalot=None,
        pushalot_notify_onsnatch=None,
        pushalot_notify_ondownload=None,
        pushalot_notify_onsubtitledownload=None,
        pushalot_authorizationtoken=None,
        use_pushbullet=None,
        pushbullet_notify_onsnatch=None,
        pushbullet_notify_ondownload=None,
        pushbullet_notify_onsubtitledownload=None,
        pushbullet_api=None,
        pushbullet_device=None,
        pushbullet_device_list=None,
        pushbullet_channel_list=None,
        pushbullet_channel=None,
        use_email=None,
        email_notify_onsnatch=None,
        email_notify_ondownload=None,
        email_notify_onpostprocess=None,
        email_notify_onsubtitledownload=None,
        email_host=None,
        email_port=25,
        email_from=None,
        email_tls=None,
        email_user=None,
        email_password=None,
        email_list=None,
        email_subject=None,
        email_show_list=None,
        email_show=None,
        use_slack=False,
        slack_notify_snatch=None,
        slack_notify_download=None,
        slack_notify_subtitledownload=None,
        slack_webhook=None,
        slack_icon_emoji=None,
        use_rocketchat=False,
        rocketchat_notify_snatch=None,
        rocketchat_notify_download=None,
        rocketchat_notify_subtitledownload=None,
        rocketchat_webhook=None,
        rocketchat_icon_emoji=None,
        use_matrix=False,
        matrix_notify_snatch=None,
        matrix_notify_download=None,
        matrix_notify_subtitledownload=None,
        matrix_api_token=None,
        matrix_server=None,
        matrix_room=None,
        use_discord=False,
        discord_notify_snatch=None,
        discord_notify_download=None,
        discord_webhook=None,
        discord_name=None,
        discord_avatar_url=None,
        discord_tts=False,
    ):

        results = []

        settings.USE_KODI = config.checkbox_to_value(use_kodi)
        settings.KODI_ALWAYS_ON = config.checkbox_to_value(kodi_always_on)
        settings.KODI_NOTIFY_ONSNATCH = config.checkbox_to_value(kodi_notify_onsnatch)
        settings.KODI_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(kodi_notify_ondownload)
        settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(kodi_notify_onsubtitledownload)
        settings.KODI_UPDATE_LIBRARY = config.checkbox_to_value(kodi_update_library)
        settings.KODI_UPDATE_FULL = config.checkbox_to_value(kodi_update_full)
        settings.KODI_UPDATE_ONLYFIRST = config.checkbox_to_value(kodi_update_onlyfirst)
        settings.KODI_HOST = config.clean_hosts(kodi_host)
        settings.KODI_USERNAME = kodi_username
        settings.KODI_PASSWORD = filters.unhide(settings.KODI_PASSWORD, kodi_password)

        settings.USE_PLEX_SERVER = config.checkbox_to_value(use_plex_server)
        settings.PLEX_NOTIFY_ONSNATCH = config.checkbox_to_value(plex_notify_onsnatch)
        settings.PLEX_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(plex_notify_ondownload)
        settings.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(plex_notify_onsubtitledownload)
        settings.PLEX_UPDATE_LIBRARY = config.checkbox_to_value(plex_update_library)
        settings.PLEX_CLIENT_HOST = config.clean_hosts(plex_client_host)
        settings.PLEX_SERVER_HOST = config.clean_hosts(plex_server_host)
        settings.PLEX_SERVER_TOKEN = config.clean_host(plex_server_token)
        settings.PLEX_SERVER_USERNAME = plex_server_username
        settings.PLEX_SERVER_PASSWORD = filters.unhide(settings.PLEX_SERVER_PASSWORD, plex_server_password)

        settings.USE_PLEX_CLIENT = config.checkbox_to_value(use_plex_client)
        settings.PLEX_CLIENT_USERNAME = plex_client_username
        settings.PLEX_CLIENT_PASSWORD = filters.unhide(settings.PLEX_CLIENT_PASSWORD, plex_client_password)
        settings.PLEX_SERVER_HTTPS = config.checkbox_to_value(plex_server_https)

        settings.USE_EMBY = config.checkbox_to_value(use_emby)
        settings.EMBY_HOST = config.clean_url(emby_host)
        settings.EMBY_APIKEY = filters.unhide(settings.EMBY_APIKEY, emby_apikey)

        settings.USE_GROWL = config.checkbox_to_value(use_growl)
        settings.GROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(growl_notify_onsnatch)
        settings.GROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(growl_notify_ondownload)
        settings.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(growl_notify_onsubtitledownload)
        settings.GROWL_HOST = config.clean_host(growl_host, default_port=23053)
        settings.GROWL_PASSWORD = filters.unhide(settings.GROWL_PASSWORD, growl_password)

        settings.USE_FREEMOBILE = config.checkbox_to_value(use_freemobile)
        settings.FREEMOBILE_NOTIFY_ONSNATCH = config.checkbox_to_value(freemobile_notify_onsnatch)
        settings.FREEMOBILE_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(freemobile_notify_ondownload)
        settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(freemobile_notify_onsubtitledownload)
        settings.FREEMOBILE_ID = freemobile_id
        settings.FREEMOBILE_APIKEY = filters.unhide(settings.FREEMOBILE_APIKEY, freemobile_apikey)

        settings.USE_TELEGRAM = config.checkbox_to_value(use_telegram)
        settings.TELEGRAM_NOTIFY_ONSNATCH = config.checkbox_to_value(telegram_notify_onsnatch)
        settings.TELEGRAM_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(telegram_notify_ondownload)
        settings.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(telegram_notify_onsubtitledownload)
        settings.TELEGRAM_ID = telegram_id
        settings.TELEGRAM_APIKEY = filters.unhide(settings.TELEGRAM_APIKEY, telegram_apikey)

        settings.USE_JOIN = config.checkbox_to_value(use_join)
        settings.JOIN_NOTIFY_ONSNATCH = config.checkbox_to_value(join_notify_onsnatch)
        settings.JOIN_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(join_notify_ondownload)
        settings.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(join_notify_onsubtitledownload)
        settings.JOIN_ID = join_id
        settings.JOIN_APIKEY = filters.unhide(settings.JOIN_APIKEY, join_apikey)

        settings.USE_PROWL = config.checkbox_to_value(use_prowl)
        settings.PROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(prowl_notify_onsnatch)
        settings.PROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(prowl_notify_ondownload)
        settings.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(prowl_notify_onsubtitledownload)
        settings.PROWL_API = prowl_api
        settings.PROWL_PRIORITY = prowl_priority
        settings.PROWL_MESSAGE_TITLE = prowl_message_title

        settings.USE_TWITTER = config.checkbox_to_value(use_twitter)
        settings.TWITTER_NOTIFY_ONSNATCH = config.checkbox_to_value(twitter_notify_onsnatch)
        settings.TWITTER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twitter_notify_ondownload)
        settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twitter_notify_onsubtitledownload)
        settings.TWITTER_USEDM = config.checkbox_to_value(twitter_usedm)
        settings.TWITTER_DMTO = twitter_dmto

        settings.USE_TWILIO = config.checkbox_to_value(use_twilio)
        settings.TWILIO_NOTIFY_ONSNATCH = config.checkbox_to_value(twilio_notify_onsnatch)
        settings.TWILIO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twilio_notify_ondownload)
        settings.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twilio_notify_onsubtitledownload)
        settings.TWILIO_PHONE_SID = twilio_phone_sid
        settings.TWILIO_ACCOUNT_SID = twilio_account_sid
        settings.TWILIO_AUTH_TOKEN = twilio_auth_token
        settings.TWILIO_TO_NUMBER = twilio_to_number

        settings.USE_SLACK = config.checkbox_to_value(use_slack)
        settings.SLACK_NOTIFY_SNATCH = config.checkbox_to_value(slack_notify_snatch)
        settings.SLACK_NOTIFY_DOWNLOAD = config.checkbox_to_value(slack_notify_download)
        settings.SLACK_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(slack_notify_subtitledownload)
        settings.SLACK_WEBHOOK = slack_webhook
        settings.SLACK_ICON_EMOJI = slack_icon_emoji

        settings.USE_ROCKETCHAT = config.checkbox_to_value(use_rocketchat)
        settings.ROCKETCHAT_NOTIFY_SNATCH = config.checkbox_to_value(rocketchat_notify_snatch)
        settings.ROCKETCHAT_NOTIFY_DOWNLOAD = config.checkbox_to_value(rocketchat_notify_download)
        settings.ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(rocketchat_notify_subtitledownload)
        settings.ROCKETCHAT_WEBHOOK = rocketchat_webhook
        settings.ROCKETCHAT_ICON_EMOJI = rocketchat_icon_emoji

        settings.USE_MATRIX = config.checkbox_to_value(use_matrix)
        settings.MATRIX_NOTIFY_SNATCH = config.checkbox_to_value(matrix_notify_snatch)
        settings.MATRIX_NOTIFY_DOWNLOAD = config.checkbox_to_value(matrix_notify_download)
        settings.MATRIX_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(matrix_notify_subtitledownload)
        settings.MATRIX_API_TOKEN = matrix_api_token
        settings.MATRIX_SERVER = matrix_server
        settings.MATRIX_ROOM = matrix_room

        settings.USE_DISCORD = config.checkbox_to_value(use_discord)
        settings.DISCORD_NOTIFY_SNATCH = config.checkbox_to_value(discord_notify_snatch)
        settings.DISCORD_NOTIFY_DOWNLOAD = config.checkbox_to_value(discord_notify_download)
        settings.DISCORD_WEBHOOK = discord_webhook
        settings.DISCORD_NAME = discord_name
        settings.DISCORD_AVATAR_URL = discord_avatar_url
        settings.DISCORD_TTS = discord_tts

        settings.USE_BOXCAR2 = config.checkbox_to_value(use_boxcar2)
        settings.BOXCAR2_NOTIFY_ONSNATCH = config.checkbox_to_value(boxcar2_notify_onsnatch)
        settings.BOXCAR2_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(boxcar2_notify_ondownload)
        settings.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(boxcar2_notify_onsubtitledownload)
        settings.BOXCAR2_ACCESSTOKEN = boxcar2_accesstoken

        settings.USE_PUSHOVER = config.checkbox_to_value(use_pushover)
        settings.PUSHOVER_NOTIFY_ONSNATCH = config.checkbox_to_value(pushover_notify_onsnatch)
        settings.PUSHOVER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushover_notify_ondownload)
        settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushover_notify_onsubtitledownload)
        settings.PUSHOVER_USERKEY = pushover_userkey
        settings.PUSHOVER_APIKEY = filters.unhide(settings.PUSHOVER_APIKEY, pushover_apikey)
        settings.PUSHOVER_DEVICE = pushover_device
        settings.PUSHOVER_SOUND = pushover_sound
        settings.PUSHOVER_PRIORITY = pushover_priority

        settings.USE_LIBNOTIFY = config.checkbox_to_value(use_libnotify)
        settings.LIBNOTIFY_NOTIFY_ONSNATCH = config.checkbox_to_value(libnotify_notify_onsnatch)
        settings.LIBNOTIFY_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(libnotify_notify_ondownload)
        settings.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(libnotify_notify_onsubtitledownload)

        settings.USE_NMJ = config.checkbox_to_value(use_nmj)
        settings.NMJ_HOST = config.clean_host(nmj_host)
        settings.NMJ_DATABASE = nmj_database
        settings.NMJ_MOUNT = nmj_mount

        settings.USE_NMJv2 = config.checkbox_to_value(use_nmjv2)
        settings.NMJv2_HOST = config.clean_host(nmjv2_host)
        settings.NMJv2_DATABASE = nmjv2_database
        settings.NMJv2_DBLOC = nmjv2_dbloc

        settings.USE_SYNOINDEX = config.checkbox_to_value(use_synoindex)

        settings.USE_SYNOLOGYNOTIFIER = config.checkbox_to_value(use_synologynotifier)
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = config.checkbox_to_value(synologynotifier_notify_onsnatch)
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(synologynotifier_notify_ondownload)
        settings.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(synologynotifier_notify_onsubtitledownload)

        config.change_use_trakt(use_trakt)
        settings.TRAKT_USERNAME = trakt_username
        settings.TRAKT_REMOVE_WATCHLIST = config.checkbox_to_value(trakt_remove_watchlist)
        settings.TRAKT_REMOVE_SERIESLIST = config.checkbox_to_value(trakt_remove_serieslist)
        settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL = config.checkbox_to_value(trakt_remove_show_from_sickchill)
        settings.TRAKT_SYNC_WATCHLIST = config.checkbox_to_value(trakt_sync_watchlist)
        settings.TRAKT_METHOD_ADD = int(trakt_method_add)
        settings.TRAKT_START_PAUSED = config.checkbox_to_value(trakt_start_paused)
        settings.TRAKT_USE_RECOMMENDED = config.checkbox_to_value(trakt_use_recommended)
        settings.TRAKT_SYNC = config.checkbox_to_value(trakt_sync)
        settings.TRAKT_SYNC_REMOVE = config.checkbox_to_value(trakt_sync_remove)
        settings.TRAKT_DEFAULT_INDEXER = int(trakt_default_indexer)
        settings.TRAKT_TIMEOUT = int(trakt_timeout)
        settings.TRAKT_BLACKLIST_NAME = trakt_blacklist_name

        settings.USE_EMAIL = config.checkbox_to_value(use_email)
        settings.EMAIL_NOTIFY_ONSNATCH = config.checkbox_to_value(email_notify_onsnatch)
        settings.EMAIL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(email_notify_ondownload)
        settings.EMAIL_NOTIFY_ONPOSTPROCESS = config.checkbox_to_value(email_notify_onpostprocess)
        settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(email_notify_onsubtitledownload)
        settings.EMAIL_HOST = config.clean_host(email_host)
        settings.EMAIL_PORT = try_int(email_port, 25)
        settings.EMAIL_FROM = email_from
        settings.EMAIL_TLS = config.checkbox_to_value(email_tls)
        settings.EMAIL_USER = email_user
        settings.EMAIL_PASSWORD = filters.unhide(settings.EMAIL_PASSWORD, email_password)
        settings.EMAIL_LIST = email_list
        settings.EMAIL_SUBJECT = email_subject

        settings.USE_PYTIVO = config.checkbox_to_value(use_pytivo)
        settings.PYTIVO_NOTIFY_ONSNATCH = config.checkbox_to_value(pytivo_notify_onsnatch)
        settings.PYTIVO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pytivo_notify_ondownload)
        settings.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pytivo_notify_onsubtitledownload)
        settings.PYTIVO_UPDATE_LIBRARY = config.checkbox_to_value(pytivo_update_library)
        settings.PYTIVO_HOST = config.clean_host(pytivo_host)
        settings.PYTIVO_SHARE_NAME = pytivo_share_name
        settings.PYTIVO_TIVO_NAME = pytivo_tivo_name

        settings.USE_PUSHALOT = config.checkbox_to_value(use_pushalot)
        settings.PUSHALOT_NOTIFY_ONSNATCH = config.checkbox_to_value(pushalot_notify_onsnatch)
        settings.PUSHALOT_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushalot_notify_ondownload)
        settings.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushalot_notify_onsubtitledownload)
        settings.PUSHALOT_AUTHORIZATIONTOKEN = pushalot_authorizationtoken

        settings.USE_PUSHBULLET = config.checkbox_to_value(use_pushbullet)
        settings.PUSHBULLET_NOTIFY_ONSNATCH = config.checkbox_to_value(pushbullet_notify_onsnatch)
        settings.PUSHBULLET_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushbullet_notify_ondownload)
        settings.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushbullet_notify_onsubtitledownload)
        settings.PUSHBULLET_API = pushbullet_api
        settings.PUSHBULLET_DEVICE = pushbullet_device_list
        settings.PUSHBULLET_CHANNEL = pushbullet_channel_list or ""

        sickchill.start.save_config()

        if results:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_("Error(s) Saving Configuration"), "<br>\n".join(results))
        else:
            ui.notifications.message(_("Configuration Saved"), os.path.join(settings.CONFIG_FILE))

        return self.redirect("/config/notifications/")
