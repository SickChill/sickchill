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
from __future__ import absolute_import, print_function, unicode_literals

# Stdlib Imports
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import config, filters, logger, ui
from sickchill.helper import try_int
from sickchill.helper.encoding import ek
from sickchill.views.common import PageTemplate
from sickchill.views.routes import Route

# Local Folder Imports
from . import Config


@Route('/config/notifications(/?.*)', name='config:notifications')
class ConfigNotifications(Config):
    def __init__(self, *args, **kwargs):
        super(ConfigNotifications, self).__init__(*args, **kwargs)

    @addslash
    def index(self, *args_, **kwargs_):
        t = PageTemplate(rh=self, filename="config_notifications.mako")

        return t.render(submenu=self.ConfigMenu(), title=_('Config - Notifications'),
                        header=_('Notifications'), topmenu='config',
                        controller="config", action="notifications")

    def saveNotifications(
            self, use_kodi=None, kodi_always_on=None, kodi_notify_onsnatch=None,
            kodi_notify_ondownload=None,
            kodi_notify_onsubtitledownload=None, kodi_update_onlyfirst=None,
            kodi_update_library=None, kodi_update_full=None, kodi_host=None, kodi_username=None,
            kodi_password=None,
            use_plex_server=None, plex_notify_onsnatch=None, plex_notify_ondownload=None,
            plex_notify_onsubtitledownload=None, plex_update_library=None,
            plex_server_host=None, plex_server_token=None, plex_client_host=None, plex_server_username=None, plex_server_password=None,
            use_plex_client=None, plex_client_username=None, plex_client_password=None,
            plex_server_https=None, use_emby=None, emby_host=None, emby_apikey=None,
            use_growl=None, growl_notify_onsnatch=None, growl_notify_ondownload=None,
            growl_notify_onsubtitledownload=None, growl_host=None, growl_password=None,
            use_freemobile=None, freemobile_notify_onsnatch=None, freemobile_notify_ondownload=None,
            freemobile_notify_onsubtitledownload=None, freemobile_id=None, freemobile_apikey=None,
            use_telegram=None, telegram_notify_onsnatch=None, telegram_notify_ondownload=None,
            telegram_notify_onsubtitledownload=None, telegram_id=None, telegram_apikey=None,
            use_join=None, join_notify_onsnatch=None, join_notify_ondownload=None,
            join_notify_onsubtitledownload=None, join_id=None, join_apikey=None,
            use_prowl=None, prowl_notify_onsnatch=None, prowl_notify_ondownload=None,
            prowl_notify_onsubtitledownload=None, prowl_api=None, prowl_priority=0,
            prowl_show_list=None, prowl_show=None, prowl_message_title=None,
            use_twitter=None, twitter_notify_onsnatch=None, twitter_notify_ondownload=None,
            twitter_notify_onsubtitledownload=None, twitter_usedm=None, twitter_dmto=None,
            use_twilio=None, twilio_notify_onsnatch=None, twilio_notify_ondownload=None, twilio_notify_onsubtitledownload=None,
            twilio_phone_sid=None, twilio_account_sid=None, twilio_auth_token=None, twilio_to_number=None,
            use_boxcar2=None, boxcar2_notify_onsnatch=None, boxcar2_notify_ondownload=None,
            boxcar2_notify_onsubtitledownload=None, boxcar2_accesstoken=None,
            use_pushover=None, pushover_notify_onsnatch=None, pushover_notify_ondownload=None,
            pushover_notify_onsubtitledownload=None, pushover_userkey=None, pushover_apikey=None,
            pushover_device=None, pushover_sound=None, pushover_priority=0,
            use_libnotify=None, libnotify_notify_onsnatch=None, libnotify_notify_ondownload=None,
            libnotify_notify_onsubtitledownload=None,
            use_nmj=None, nmj_host=None, nmj_database=None, nmj_mount=None, use_synoindex=None,
            use_nmjv2=None, nmjv2_host=None, nmjv2_dbloc=None, nmjv2_database=None,
            use_trakt=None, trakt_username=None, trakt_pin=None,
            trakt_remove_watchlist=None, trakt_sync_watchlist=None, trakt_remove_show_from_sickchill=None, trakt_method_add=None,
            trakt_start_paused=None, trakt_use_recommended=None, trakt_sync=None, trakt_sync_remove=None,
            trakt_default_indexer=None, trakt_remove_serieslist=None, trakt_timeout=None, trakt_blacklist_name=None,
            use_synologynotifier=None, synologynotifier_notify_onsnatch=None,
            synologynotifier_notify_ondownload=None, synologynotifier_notify_onsubtitledownload=None,
            use_pytivo=None, pytivo_notify_onsnatch=None, pytivo_notify_ondownload=None,
            pytivo_notify_onsubtitledownload=None, pytivo_update_library=None,
            pytivo_host=None, pytivo_share_name=None, pytivo_tivo_name=None,
            use_pushalot=None, pushalot_notify_onsnatch=None, pushalot_notify_ondownload=None,
            pushalot_notify_onsubtitledownload=None, pushalot_authorizationtoken=None,
            use_pushbullet=None, pushbullet_notify_onsnatch=None, pushbullet_notify_ondownload=None,
            pushbullet_notify_onsubtitledownload=None, pushbullet_api=None, pushbullet_device=None,
            pushbullet_device_list=None, pushbullet_channel_list=None, pushbullet_channel=None,
            use_email=None, email_notify_onsnatch=None, email_notify_ondownload=None, email_notify_onpostprocess=None,
            email_notify_onsubtitledownload=None, email_host=None, email_port=25, email_from=None,
            email_tls=None, email_user=None, email_password=None, email_list=None, email_subject=None, email_show_list=None,
            email_show=None, use_slack=False, slack_notify_snatch=None, slack_notify_download=None, slack_notify_subtitledownload=None, slack_webhook=None, slack_icon_emoji=None,
            use_matrix=False, matrix_notify_snatch=None, matrix_notify_download=None, matrix_notify_subtitledownload=None,
            matrix_api_token=None, matrix_server=None, matrix_room=None,
            use_discord=False, discord_notify_snatch=None, discord_notify_download=None, discord_webhook=None, discord_name=None,
            discord_avatar_url=None, discord_tts=False):

        results = []

        sickbeard.USE_KODI = config.checkbox_to_value(use_kodi)
        sickbeard.KODI_ALWAYS_ON = config.checkbox_to_value(kodi_always_on)
        sickbeard.KODI_NOTIFY_ONSNATCH = config.checkbox_to_value(kodi_notify_onsnatch)
        sickbeard.KODI_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(kodi_notify_ondownload)
        sickbeard.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(kodi_notify_onsubtitledownload)
        sickbeard.KODI_UPDATE_LIBRARY = config.checkbox_to_value(kodi_update_library)
        sickbeard.KODI_UPDATE_FULL = config.checkbox_to_value(kodi_update_full)
        sickbeard.KODI_UPDATE_ONLYFIRST = config.checkbox_to_value(kodi_update_onlyfirst)
        sickbeard.KODI_HOST = config.clean_hosts(kodi_host)
        sickbeard.KODI_USERNAME = kodi_username
        sickbeard.KODI_PASSWORD = filters.unhide(sickbeard.KODI_PASSWORD, kodi_password)

        sickbeard.USE_PLEX_SERVER = config.checkbox_to_value(use_plex_server)
        sickbeard.PLEX_NOTIFY_ONSNATCH = config.checkbox_to_value(plex_notify_onsnatch)
        sickbeard.PLEX_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(plex_notify_ondownload)
        sickbeard.PLEX_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(plex_notify_onsubtitledownload)
        sickbeard.PLEX_UPDATE_LIBRARY = config.checkbox_to_value(plex_update_library)
        sickbeard.PLEX_CLIENT_HOST = config.clean_hosts(plex_client_host)
        sickbeard.PLEX_SERVER_HOST = config.clean_hosts(plex_server_host)
        sickbeard.PLEX_SERVER_TOKEN = config.clean_host(plex_server_token)
        sickbeard.PLEX_SERVER_USERNAME = plex_server_username
        sickbeard.PLEX_SERVER_PASSWORD = filters.unhide(sickbeard.PLEX_SERVER_PASSWORD, plex_server_password)

        sickbeard.USE_PLEX_CLIENT = config.checkbox_to_value(use_plex_client)
        sickbeard.PLEX_CLIENT_USERNAME = plex_client_username
        sickbeard.PLEX_CLIENT_PASSWORD = filters.unhide(sickbeard.PLEX_CLIENT_PASSWORD, plex_client_password)
        sickbeard.PLEX_SERVER_HTTPS = config.checkbox_to_value(plex_server_https)

        sickbeard.USE_EMBY = config.checkbox_to_value(use_emby)
        sickbeard.EMBY_HOST = config.clean_host(emby_host)
        sickbeard.EMBY_APIKEY = filters.unhide(sickbeard.EMBY_APIKEY, emby_apikey)

        sickbeard.USE_GROWL = config.checkbox_to_value(use_growl)
        sickbeard.GROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(growl_notify_onsnatch)
        sickbeard.GROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(growl_notify_ondownload)
        sickbeard.GROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(growl_notify_onsubtitledownload)
        sickbeard.GROWL_HOST = config.clean_host(growl_host, default_port=23053)
        sickbeard.GROWL_PASSWORD = filters.unhide(sickbeard.GROWL_PASSWORD, growl_password)

        sickbeard.USE_FREEMOBILE = config.checkbox_to_value(use_freemobile)
        sickbeard.FREEMOBILE_NOTIFY_ONSNATCH = config.checkbox_to_value(freemobile_notify_onsnatch)
        sickbeard.FREEMOBILE_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(freemobile_notify_ondownload)
        sickbeard.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(freemobile_notify_onsubtitledownload)
        sickbeard.FREEMOBILE_ID = freemobile_id
        sickbeard.FREEMOBILE_APIKEY = filters.unhide(sickbeard.FREEMOBILE_APIKEY, freemobile_apikey)

        sickbeard.USE_TELEGRAM = config.checkbox_to_value(use_telegram)
        sickbeard.TELEGRAM_NOTIFY_ONSNATCH = config.checkbox_to_value(telegram_notify_onsnatch)
        sickbeard.TELEGRAM_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(telegram_notify_ondownload)
        sickbeard.TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(telegram_notify_onsubtitledownload)
        sickbeard.TELEGRAM_ID = telegram_id
        sickbeard.TELEGRAM_APIKEY = filters.unhide(sickbeard.TELEGRAM_APIKEY, telegram_apikey)

        sickbeard.USE_JOIN = config.checkbox_to_value(use_join)
        sickbeard.JOIN_NOTIFY_ONSNATCH = config.checkbox_to_value(join_notify_onsnatch)
        sickbeard.JOIN_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(join_notify_ondownload)
        sickbeard.JOIN_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(join_notify_onsubtitledownload)
        sickbeard.JOIN_ID = join_id
        sickbeard.JOIN_APIKEY = filters.unhide(sickbeard.JOIN_APIKEY, join_apikey)

        sickbeard.USE_PROWL = config.checkbox_to_value(use_prowl)
        sickbeard.PROWL_NOTIFY_ONSNATCH = config.checkbox_to_value(prowl_notify_onsnatch)
        sickbeard.PROWL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(prowl_notify_ondownload)
        sickbeard.PROWL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(prowl_notify_onsubtitledownload)
        sickbeard.PROWL_API = prowl_api
        sickbeard.PROWL_PRIORITY = prowl_priority
        sickbeard.PROWL_MESSAGE_TITLE = prowl_message_title

        sickbeard.USE_TWITTER = config.checkbox_to_value(use_twitter)
        sickbeard.TWITTER_NOTIFY_ONSNATCH = config.checkbox_to_value(twitter_notify_onsnatch)
        sickbeard.TWITTER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twitter_notify_ondownload)
        sickbeard.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twitter_notify_onsubtitledownload)
        sickbeard.TWITTER_USEDM = config.checkbox_to_value(twitter_usedm)
        sickbeard.TWITTER_DMTO = twitter_dmto

        sickbeard.USE_TWILIO = config.checkbox_to_value(use_twilio)
        sickbeard.TWILIO_NOTIFY_ONSNATCH = config.checkbox_to_value(twilio_notify_onsnatch)
        sickbeard.TWILIO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(twilio_notify_ondownload)
        sickbeard.TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(twilio_notify_onsubtitledownload)
        sickbeard.TWILIO_PHONE_SID = twilio_phone_sid
        sickbeard.TWILIO_ACCOUNT_SID = twilio_account_sid
        sickbeard.TWILIO_AUTH_TOKEN = twilio_auth_token
        sickbeard.TWILIO_TO_NUMBER = twilio_to_number

        sickbeard.USE_SLACK = config.checkbox_to_value(use_slack)
        sickbeard.SLACK_NOTIFY_SNATCH = config.checkbox_to_value(slack_notify_snatch)
        sickbeard.SLACK_NOTIFY_DOWNLOAD = config.checkbox_to_value(slack_notify_download)
        sickbeard.SLACK_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(slack_notify_subtitledownload)
        sickbeard.SLACK_WEBHOOK = slack_webhook
        sickbeard.SLACK_ICON_EMOJI = slack_icon_emoji

        sickbeard.USE_MATRIX = config.checkbox_to_value(use_matrix)
        sickbeard.MATRIX_NOTIFY_SNATCH = config.checkbox_to_value(matrix_notify_snatch)
        sickbeard.MATRIX_NOTIFY_DOWNLOAD = config.checkbox_to_value(matrix_notify_download)
        sickbeard.MATRIX_NOTIFY_SUBTITLEDOWNLOAD = config.checkbox_to_value(matrix_notify_subtitledownload)
        sickbeard.MATRIX_API_TOKEN = matrix_api_token
        sickbeard.MATRIX_SERVER = matrix_server
        sickbeard.MATRIX_ROOM = matrix_room

        sickbeard.USE_DISCORD = config.checkbox_to_value(use_discord)
        sickbeard.DISCORD_NOTIFY_SNATCH = config.checkbox_to_value(discord_notify_snatch)
        sickbeard.DISCORD_NOTIFY_DOWNLOAD = config.checkbox_to_value(discord_notify_download)
        sickbeard.DISCORD_WEBHOOK = discord_webhook
        sickbeard.DISCORD_NAME = discord_name
        sickbeard.DISCORD_AVATAR_URL = discord_avatar_url
        sickbeard.DISCORD_TTS = discord_tts

        sickbeard.USE_BOXCAR2 = config.checkbox_to_value(use_boxcar2)
        sickbeard.BOXCAR2_NOTIFY_ONSNATCH = config.checkbox_to_value(boxcar2_notify_onsnatch)
        sickbeard.BOXCAR2_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(boxcar2_notify_ondownload)
        sickbeard.BOXCAR2_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(boxcar2_notify_onsubtitledownload)
        sickbeard.BOXCAR2_ACCESSTOKEN = boxcar2_accesstoken

        sickbeard.USE_PUSHOVER = config.checkbox_to_value(use_pushover)
        sickbeard.PUSHOVER_NOTIFY_ONSNATCH = config.checkbox_to_value(pushover_notify_onsnatch)
        sickbeard.PUSHOVER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushover_notify_ondownload)
        sickbeard.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushover_notify_onsubtitledownload)
        sickbeard.PUSHOVER_USERKEY = pushover_userkey
        sickbeard.PUSHOVER_APIKEY = filters.unhide(sickbeard.PUSHOVER_APIKEY, pushover_apikey)
        sickbeard.PUSHOVER_DEVICE = pushover_device
        sickbeard.PUSHOVER_SOUND = pushover_sound
        sickbeard.PUSHOVER_PRIORITY = pushover_priority

        sickbeard.USE_LIBNOTIFY = config.checkbox_to_value(use_libnotify)
        sickbeard.LIBNOTIFY_NOTIFY_ONSNATCH = config.checkbox_to_value(libnotify_notify_onsnatch)
        sickbeard.LIBNOTIFY_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(libnotify_notify_ondownload)
        sickbeard.LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(libnotify_notify_onsubtitledownload)

        sickbeard.USE_NMJ = config.checkbox_to_value(use_nmj)
        sickbeard.NMJ_HOST = config.clean_host(nmj_host)
        sickbeard.NMJ_DATABASE = nmj_database
        sickbeard.NMJ_MOUNT = nmj_mount

        sickbeard.USE_NMJv2 = config.checkbox_to_value(use_nmjv2)
        sickbeard.NMJv2_HOST = config.clean_host(nmjv2_host)
        sickbeard.NMJv2_DATABASE = nmjv2_database
        sickbeard.NMJv2_DBLOC = nmjv2_dbloc

        sickbeard.USE_SYNOINDEX = config.checkbox_to_value(use_synoindex)

        sickbeard.USE_SYNOLOGYNOTIFIER = config.checkbox_to_value(use_synologynotifier)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH = config.checkbox_to_value(synologynotifier_notify_onsnatch)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(synologynotifier_notify_ondownload)
        sickbeard.SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(
            synologynotifier_notify_onsubtitledownload)

        config.change_use_trakt(use_trakt)
        sickbeard.TRAKT_USERNAME = trakt_username
        sickbeard.TRAKT_REMOVE_WATCHLIST = config.checkbox_to_value(trakt_remove_watchlist)
        sickbeard.TRAKT_REMOVE_SERIESLIST = config.checkbox_to_value(trakt_remove_serieslist)
        sickbeard.TRAKT_REMOVE_SHOW_FROM_SICKCHILL = config.checkbox_to_value(trakt_remove_show_from_sickchill)
        sickbeard.TRAKT_SYNC_WATCHLIST = config.checkbox_to_value(trakt_sync_watchlist)
        sickbeard.TRAKT_METHOD_ADD = int(trakt_method_add)
        sickbeard.TRAKT_START_PAUSED = config.checkbox_to_value(trakt_start_paused)
        sickbeard.TRAKT_USE_RECOMMENDED = config.checkbox_to_value(trakt_use_recommended)
        sickbeard.TRAKT_SYNC = config.checkbox_to_value(trakt_sync)
        sickbeard.TRAKT_SYNC_REMOVE = config.checkbox_to_value(trakt_sync_remove)
        sickbeard.TRAKT_DEFAULT_INDEXER = int(trakt_default_indexer)
        sickbeard.TRAKT_TIMEOUT = int(trakt_timeout)
        sickbeard.TRAKT_BLACKLIST_NAME = trakt_blacklist_name

        sickbeard.USE_EMAIL = config.checkbox_to_value(use_email)
        sickbeard.EMAIL_NOTIFY_ONSNATCH = config.checkbox_to_value(email_notify_onsnatch)
        sickbeard.EMAIL_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(email_notify_ondownload)
        sickbeard.EMAIL_NOTIFY_ONPOSTPROCESS = config.checkbox_to_value(email_notify_onpostprocess)
        sickbeard.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(email_notify_onsubtitledownload)
        sickbeard.EMAIL_HOST = config.clean_host(email_host)
        sickbeard.EMAIL_PORT = try_int(email_port, 25)
        sickbeard.EMAIL_FROM = email_from
        sickbeard.EMAIL_TLS = config.checkbox_to_value(email_tls)
        sickbeard.EMAIL_USER = email_user
        sickbeard.EMAIL_PASSWORD = filters.unhide(sickbeard.EMAIL_PASSWORD, email_password)
        sickbeard.EMAIL_LIST = email_list
        sickbeard.EMAIL_SUBJECT = email_subject

        sickbeard.USE_PYTIVO = config.checkbox_to_value(use_pytivo)
        sickbeard.PYTIVO_NOTIFY_ONSNATCH = config.checkbox_to_value(pytivo_notify_onsnatch)
        sickbeard.PYTIVO_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pytivo_notify_ondownload)
        sickbeard.PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pytivo_notify_onsubtitledownload)
        sickbeard.PYTIVO_UPDATE_LIBRARY = config.checkbox_to_value(pytivo_update_library)
        sickbeard.PYTIVO_HOST = config.clean_host(pytivo_host)
        sickbeard.PYTIVO_SHARE_NAME = pytivo_share_name
        sickbeard.PYTIVO_TIVO_NAME = pytivo_tivo_name

        sickbeard.USE_PUSHALOT = config.checkbox_to_value(use_pushalot)
        sickbeard.PUSHALOT_NOTIFY_ONSNATCH = config.checkbox_to_value(pushalot_notify_onsnatch)
        sickbeard.PUSHALOT_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushalot_notify_ondownload)
        sickbeard.PUSHALOT_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushalot_notify_onsubtitledownload)
        sickbeard.PUSHALOT_AUTHORIZATIONTOKEN = pushalot_authorizationtoken

        sickbeard.USE_PUSHBULLET = config.checkbox_to_value(use_pushbullet)
        sickbeard.PUSHBULLET_NOTIFY_ONSNATCH = config.checkbox_to_value(pushbullet_notify_onsnatch)
        sickbeard.PUSHBULLET_NOTIFY_ONDOWNLOAD = config.checkbox_to_value(pushbullet_notify_ondownload)
        sickbeard.PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD = config.checkbox_to_value(pushbullet_notify_onsubtitledownload)
        sickbeard.PUSHBULLET_API = pushbullet_api
        sickbeard.PUSHBULLET_DEVICE = pushbullet_device_list
        sickbeard.PUSHBULLET_CHANNEL = pushbullet_channel_list or ""

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.log(x, logger.ERROR)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), ek(os.path.join, sickbeard.CONFIG_FILE))

        return self.redirect("/config/notifications/")
