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
import os

# Third Party Imports
from tornado.web import addslash

# First Party Imports
import sickbeard
from sickbeard import config, filters, logger, ui
from sickchill.helper import try_int
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

    def saveNotifications(self):

        results = []

        from sickchill.providers.notifications import set_config, get_config

        data = self.request.body_arguments

        set_config('kodi', 'enable', config.checkbox_to_value(data['use_kodi']))
        set_config('kodi', 'always_on', config.checkbox_to_value(data['kodi_always_on']))
        set_config('kodi', 'snatch', config.checkbox_to_value(data['kodi_notify_snatch']))
        set_config('kodi', 'download', config.checkbox_to_value(data['kodi_notify_download']))
        set_config('kodi', 'subtitle', config.checkbox_to_value(data['kodi_notify_subtitle_download']))
        set_config('kodi', 'update', config.checkbox_to_value(data['kodi_notify_library']))
        set_config('kodi', 'update', config.checkbox_to_value(data['kodi_notify_full']))
        set_config('kodi', 'update', config.checkbox_to_value(data['kodi_notify_onlyfirst']))
        set_config('kodi', 'host', config.clean_hosts(data['kodi_host']))
        set_config('kodi', 'username', data['kodi_username'])
        set_config('kodi', 'password', filters.unhide(get_config('kodi', 'password'), data['kodi_password']))

        set_config('plex', 'server', config.checkbox_to_value(data['use_plex_server']))
        set_config('plex', 'client', config.checkbox_to_value(data['use_plex_client']))
        set_config('plex', 'https', config.checkbox_to_value(data['plex_server_https']))

        set_config('plex', 'snatch', config.checkbox_to_value(data['plex_notify_snatch']))
        set_config('plex', 'download', config.checkbox_to_value(data['plex_notify_download']))
        set_config('plex', 'subtitle', config.checkbox_to_value(data['plex_notify_subtitle_download']))
        set_config('plex', 'update', config.checkbox_to_value(data['plex_notify_library']))
        set_config('plex', 'client_host', config.clean_hosts(data['plex_client_host']))
        set_config('plex', 'server_host', config.clean_hosts(data['plex_server_host']))
        set_config('plex', 'server_token', data['plex_server_token'])
        set_config('plex', 'username', data['plex_server_username'])
        set_config('plex', 'password', data['plex_server_password'])

        set_config('emby', 'enable', config.checkbox_to_value(data['use_emby']))
        set_config('emby', 'host', config.clean_url(data['emby_host']))
        set_config('emby', 'apikey', data['emby_apikey'])

        set_config('growl', 'enable', config.checkbox_to_value(data['use_growl']))
        set_config('growl', 'snatch', config.checkbox_to_value(data['growl_notify_snatch']))
        set_config('growl', 'download', config.checkbox_to_value(data['growl_notify_download']))
        set_config('growl', 'subtitle', config.checkbox_to_value(data['growl_notify_subtitle_download']))
        set_config('growl', 'host', config.clean_host(data['growl_host'], default_port=23053))
        set_config('growl', 'password', data['growl_password'])

        set_config('freemobile', 'enable', config.checkbox_to_value(data['use_freemobile']))
        set_config('freemobile', 'snatch', config.checkbox_to_value(data['freemobile_notify_snatch']))
        set_config('freemobile', 'download', config.checkbox_to_value(data['freemobile_notify_download']))
        set_config('freemobile', 'subtitle', config.checkbox_to_value(data['freemobile_notify_subtitle_download']))
        set_config('freemobile', 'id', data['freemobile_id'])
        set_config('freemobile', 'apikey', data['freemobile_apikey'])

        set_config('telegram', 'enable', config.checkbox_to_value(data['use_telegram']))
        set_config('telegram', 'snatch', config.checkbox_to_value(data['telegram_notify_snatch']))
        set_config('telegram', 'download', config.checkbox_to_value(data['telegram_notify_download']))
        set_config('telegram', 'subtitle', config.checkbox_to_value(data['telegram_notify_subtitle_download']))
        set_config('telegram', 'id', data['telegram_id'])
        set_config('telegram', 'apikey', data['telegram_apikey'])

        set_config('join', 'enable', config.checkbox_to_value(data['use_join']))
        set_config('join', 'snatch', config.checkbox_to_value(data['join_notify_snatch']))
        set_config('join', 'download', config.checkbox_to_value(data['join_notify_download']))
        set_config('join', 'subtitle', config.checkbox_to_value(data['join_notify_subtitle_download']))
        set_config('join', 'id', data['join_id'])
        set_config('join', 'apikey', data['join_apikey'])

        set_config('prowl', 'enable', config.checkbox_to_value(data['use_prowl']))
        set_config('prowl', 'snatch', config.checkbox_to_value(data['prowl_notify_snatch']))
        set_config('prowl', 'download', config.checkbox_to_value(data['prowl_notify_download']))
        set_config('prowl', 'subtitle', config.checkbox_to_value(data['prowl_notify_subtitle_download']))
        set_config('prowl', 'api', data['prowl_api'])
        set_config('prowl', 'priority', data['prowl_priority'])
        set_config('prowl', 'message_title', data['prowl_message_title'])

        set_config('twitter', 'enable', config.checkbox_to_value(data['use_twitter']))
        set_config('twitter', 'snatch', config.checkbox_to_value(data['twitter_notify_snatch']))
        set_config('twitter', 'download', config.checkbox_to_value(data['twitter_notify_download']))
        set_config('twitter', 'subtitle', config.checkbox_to_value(data['twitter_notify_subtitle_download']))
        set_config('twitter', 'use_dm', config.checkbox_to_value(data['twitter_usedm']))
        set_config('twitter', 'dm_to', data['twitter_dmto'])

        set_config('twilio', 'enable', config.checkbox_to_value(data['use_twilio']))
        set_config('twilio', 'snatch', config.checkbox_to_value(data['twilio_notify_snatch']))
        set_config('twilio', 'download', config.checkbox_to_value(data['twilio_notify_download']))
        set_config('twilio', 'subtitle', config.checkbox_to_value(data['twilio_notify_subtitle_download']))
        set_config('twilio', 'phone_sid', data['twilio_phone_sid'])
        set_config('twilio', 'account_sid', data['twilio_account_sid'])
        set_config('twilio', 'auth_token', data['twilio_auth_token'])
        set_config('twilio', 'to_number', data['twilio_to_number'])

        set_config('slack', 'enable', config.checkbox_to_value(data['use_slack']))
        set_config('slack', 'snatch', config.checkbox_to_value(data['slack_notify_snatch']))
        set_config('slack', 'download', config.checkbox_to_value(data['slack_notify_download']))
        set_config('slack', 'subtitledownload', config.checkbox_to_value(data['slack_notify_subtitledownload']))
        set_config('slack', 'webhook', data['slack_webhook'])
        set_config('slack', 'icon_emoji', data['slack_icon_emoji'])

        set_config('rocketchat', 'enable', config.checkbox_to_value(data['use_rocketchat']))
        set_config('rocketchat', 'snatch', config.checkbox_to_value(data['rocketchat_notify_snatch']))
        set_config('rocketchat', 'download', config.checkbox_to_value(data['rocketchat_notify_download']))
        set_config('rocketchat', 'subtitledownload', config.checkbox_to_value(data['rocketchat_notify_subtitledownload']))
        set_config('rocketchat', 'webhook', data['rocketchat_webhook'])
        set_config('rocketchat', 'icon_emoji', data['rocketchat_icon_emoji'])

        set_config('matrix', 'enable', config.checkbox_to_value(data['use_matrix']))
        set_config('matrix', 'snatch', config.checkbox_to_value(data['matrix_notify_snatch']))
        set_config('matrix', 'download', config.checkbox_to_value(data['matrix_notify_download']))
        set_config('matrix', 'subtitledownload', config.checkbox_to_value(data['matrix_notify_subtitledownload']))
        set_config('matrix', 'api_token', data['matrix_api_token'])
        set_config('matrix', 'server', data['matrix_server'])
        set_config('matrix', 'room', data['matrix_room'])

        set_config('discord', 'enable', config.checkbox_to_value(data['use_discord']))
        set_config('discord', 'snatch', config.checkbox_to_value(data['discord_notify_snatch']))
        set_config('discord', 'download', config.checkbox_to_value(data['discord_notify_download']))
        set_config('discord', 'webhook', data['discord_webhook'])
        set_config('discord', 'name', data['discord_name'])
        set_config('discord', 'avatar_url', data['discord_avatar_url'])
        set_config('discord', 'tts', data['discord_tts'])

        set_config('boxcar2', 'enable', config.checkbox_to_value(data['use_boxcar2']))
        set_config('boxcar2', 'snatch', config.checkbox_to_value(data['boxcar2_notify_snatch']))
        set_config('boxcar2', 'download', config.checkbox_to_value(data['boxcar2_notify_download']))
        set_config('boxcar2', 'subtitle', config.checkbox_to_value(data['boxcar2_notify_subtitle_download']))
        set_config('boxcar2', 'token', data['boxcar2_accesstoken'])

        set_config('pushover', 'enable', config.checkbox_to_value(data['use_pushover']))
        set_config('pushover', 'snatch', config.checkbox_to_value(data['pushover_notify_snatch']))
        set_config('pushover', 'download', config.checkbox_to_value(data['pushover_notify_download']))
        set_config('pushover', 'subtitle', config.checkbox_to_value(data['pushover_notify_subtitle_download']))
        set_config('pushover', 'userkey', data['pushover_userkey'])
        set_config('pushover', 'apikey', data['pushover_apikey'])
        set_config('pushover', 'device', data['pushover_device'])
        set_config('pushover', 'sound', data['pushover_sound'])
        set_config('pushover', 'priority', data['pushover_priority'])

        set_config('libnotify', 'enable', config.checkbox_to_value(data['use_libnotify']))
        set_config('libnotify', 'snatch', config.checkbox_to_value(data['libnotify_notify_snatch']))
        set_config('libnotify', 'download', config.checkbox_to_value(data['libnotify_notify_download']))
        set_config('libnotify', 'subtitle', config.checkbox_to_value(data['libnotify_notify_subtitle_download']))

        set_config('nmj', 'enable', config.checkbox_to_value(data['use_nmj']))
        set_config('nmj', 'host', config.clean_host(data['nmj_host']))
        set_config('nmj', 'database', data['nmj_database'])
        set_config('nmj', 'mount', data['nmj_mount'])

        set_config('nmj2', 'enable', config.checkbox_to_value(data['use_nmjv2']))
        set_config('nmj2', 'host', config.clean_host(data['nmjv2_host']))
        set_config('nmj2', 'database', data['nmjv2_database'])
        set_config('nmj2', 'dbloc', data['nmjv2_dbloc'])

        set_config('synoindex', 'enable', config.checkbox_to_value(data['use_synoindex']))

        set_config('synologynotifier', 'enable', config.checkbox_to_value(data['use_synologynotifier']))
        set_config('synologynotifier', 'snatch', config.checkbox_to_value(data['synologynotifier_notify_snatch']))
        set_config('synologynotifier', 'download', config.checkbox_to_value(data['synologynotifier_notify_download']))
        set_config('synologynotifier', 'subtitle', config.checkbox_to_value(data['synologynotifier_notify_subtitle_download']))

        config.change_use_trakt(data['use_trakt'])
        set_config('trakt', 'enable', data['use_trakt'])
        set_config('trakt', 'username', data['trakt_username'])
        set_config('trakt', 'remove_watchlist', config.checkbox_to_value(data['trakt_remove_watchlist']))
        set_config('trakt', 'remove_serieslist', config.checkbox_to_value(data['trakt_remove_serieslist']))
        set_config('trakt', 'remove_show_from_sickchill', config.checkbox_to_value(data['trakt_remove_show_from_sickchill']))
        set_config('trakt', 'sync_watchlist', config.checkbox_to_value(data['trakt_sync_watchlist']))
        set_config('trakt', 'method_add', int(data['trakt_method_add']))
        set_config('trakt', 'start_paused', config.checkbox_to_value(data['trakt_start_paused']))
        set_config('trakt', 'use_recommended', config.checkbox_to_value(data['trakt_use_recommended']))
        set_config('trakt', 'sync', config.checkbox_to_value(data['trakt_sync']))
        set_config('trakt', 'sync_remove', config.checkbox_to_value(data['trakt_sync_remove']))
        set_config('trakt', 'default_indexer', int(data['trakt_default_indexer']))
        set_config('trakt', 'timeout', int(data['trakt_timeout']))
        set_config('trakt', 'blacklist_name', data['trakt_blacklist_name'])

        set_config('email', 'enable', config.checkbox_to_value(data['use_email']))
        set_config('email', 'snatch', config.checkbox_to_value(data['email_notify_snatch']))
        set_config('email', 'download', config.checkbox_to_value(data['email_notify_download']))
        set_config('email', 'onpostprocess', config.checkbox_to_value(data['email_notify_onpostprocess']))
        set_config('email', 'subtitle', config.checkbox_to_value(data['email_notify_subtitle_download']))
        set_config('email', 'host', config.clean_host(data['email_host']))
        set_config('try', 'int', try_int(data['email_port'], 25))
        set_config('email', 'from', data['email_from'])
        set_config('email', 'tls', config.checkbox_to_value(data['email_tls']))
        set_config('email', 'user', data['email_user'])
        set_config('email', 'password', data['email_password'])
        set_config('email', 'list', data['email_list'])
        set_config('email', 'show', data['email_show'])
        set_config('email', 'show_list', data['email_show_list'])
        set_config('email', 'subject', data['email_subject'])

        set_config('pytivo', 'enable', config.checkbox_to_value(data['use_pytivo']))
        set_config('pytivo', 'snatch', config.checkbox_to_value(data['pytivo_notify_snatch']))
        set_config('pytivo', 'download', config.checkbox_to_value(data['pytivo_notify_download']))
        set_config('pytivo', 'subtitle', config.checkbox_to_value(data['pytivo_notify_subtitle_download']))
        set_config('pytivo', 'update', config.checkbox_to_value(data['pytivo_notify_library']))
        set_config('pytivo', 'host', config.clean_host(data['pytivo_host']))
        set_config('pytivo', 'share', data['pytivo_share_name'])
        set_config('pytivo', 'name', data['pytivo_tivo_name'])

        set_config('pushalot', 'enable', config.checkbox_to_value(data['use_pushalot']))
        set_config('pushalot', 'snatch', config.checkbox_to_value(data['pushalot_notify_snatch']))
        set_config('pushalot', 'download', config.checkbox_to_value(data['pushalot_notify_download']))
        set_config('pushalot', 'subtitle', config.checkbox_to_value(data['pushalot_notify_subtitle_download']))
        set_config('pushalot', 'authorizationtoken', data['pushalot_authorizationtoken'])

        set_config('pushbullet', 'enable', config.checkbox_to_value(data['use_pushbullet']))
        set_config('pushbullet', 'snatch', config.checkbox_to_value(data['pushbullet_notify_snatch']))
        set_config('pushbullet', 'download', config.checkbox_to_value(data['pushbullet_notify_download']))
        set_config('pushbullet', 'subtitle', config.checkbox_to_value(data['pushbullet_notify_subtitle_download']))
        set_config('pushbullet', 'api', data['pushbullet_api'])
        set_config('pushbullet', 'device_list', data['pushbullet_device_list'])
        set_config('pushbullet', 'channel_list', data['pushbullet_channel_list']  or "")

        sickbeard.save_config()

        if len(results) > 0:
            for x in results:
                logger.exception(x)
            ui.notifications.error(_('Error(s) Saving Configuration'),
                                   '<br>\n'.join(results))
        else:
            ui.notifications.message(_('Configuration Saved'), os.path.join(sickbeard.CONFIG_FILE))

        return self.redirect("/config/notifications/")
