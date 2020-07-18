# coding=utf-8
# Author: Dustyn Gibson <miigotu@gmail.com>
#
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
# Third Party Imports
from subliminal.extensions import RegistrableExtensionManager

# First Party Imports
import sickbeard
from sickbeard.filters import unhide


manager = RegistrableExtensionManager('sickchill.providers.notifications', [
    'plex = sickchill.providers.notifications.plex:Notifier',
    'synoindex = sickchill.providers.notifications.synoindex:Notifier',
    'telegram = sickchill.providers.notifications.telegram:Notifier',
    'trakt = sickchill.providers.notifications.trakt:Notifier',
    'join = sickchill.providers.notifications.join:Notifier',
    'growl = sickchill.providers.notifications.growl:Notifier',
    'emby = sickchill.providers.notifications.emby:Notifier',
    'pushbullet = sickchill.providers.notifications.pushbullet:Notifier',
    'nmjv2 = sickchill.providers.notifications.nmjv2:Notifier',
    'tweet = sickchill.providers.notifications.tweet:Notifier',
    'growl = sickchill.providers.notifications.growl:Notifier',
    'pushalot = sickchill.providers.notifications.pushalot:Notifier',
    'emailnotify = sickchill.providers.notifications.emailnotify:Notifier',
    'prowl = sickchill.providers.notifications.prowl:Notifier',
    'boxcar2 = sickchill.providers.notifications.boxcar2:Notifier',
    'pytivo = sickchill.providers.notifications.pytivo:Notifier',
    'boxcar2 = sickchill.providers.notifications.boxcar2:Notifier',
    'nmj = sickchill.providers.notifications.nmj:Notifier',
    'synologynotifier = sickchill.providers.notifications.synologynotifier:Notifier',
    'matrix = sickchill.providers.notifications.matrix:Notifier',
    'rocketchat = sickchill.providers.notifications.rocketchat:Notifier',
    'trakt = sickchill.providers.notifications.trakt:Notifier',
    'libnotify = sickchill.providers.notifications.libnotify:Notifier',
    'rocketchat = sickchill.providers.notifications.rocketchat:Notifier',
    'discord = sickchill.providers.notifications.discord:Notifier',
    'pushbullet = sickchill.providers.notifications.pushbullet:Notifier',
    'twilio_notify = sickchill.providers.notifications.twilio_notify:Notifier',
    'tweet = sickchill.providers.notifications.tweet:Notifier',
    'synologynotifier = sickchill.providers.notifications.synologynotifier:Notifier',
    'plex = sickchill.providers.notifications.plex:Notifier',
    'twilio_notify = sickchill.providers.notifications.twilio_notify:Notifier',
    'discord = sickchill.providers.notifications.discord:Notifier',
    'freemobile = sickchill.providers.notifications.freemobile:Notifier',
    'slack = sickchill.providers.notifications.slack:Notifier',
    'matrix = sickchill.providers.notifications.matrix:Notifier',
    'synoindex = sickchill.providers.notifications.synoindex:Notifier',
    'kodi = sickchill.providers.notifications.kodi:Notifier',
    'nmjv2 = sickchill.providers.notifications.nmjv2:Notifier',
    'emailnotify = sickchill.providers.notifications.emailnotify:Notifier',
    'kodi = sickchill.providers.notifications.kodi:Notifier',
    'pushalot = sickchill.providers.notifications.pushalot:Notifier',
    'prowl = sickchill.providers.notifications.prowl:Notifier',
    'pushover = sickchill.providers.notifications.pushover:Notifier',
    'telegram = sickchill.providers.notifications.telegram:Notifier',
    'pytivo = sickchill.providers.notifications.pytivo:Notifier',
    'join = sickchill.providers.notifications.join:Notifier',
    'pushover = sickchill.providers.notifications.pushover:Notifier',
    'base = sickchill.providers.notifications.base:Notifier',
    'emby = sickchill.providers.notifications.emby:Notifier',
    'slack = sickchill.providers.notifications.slack:Notifier',
    'freemobile = sickchill.providers.notifications.freemobile:Notifier',
    'libnotify = sickchill.providers.notifications.libnotify:Notifier',
    'nmj = sickchill.providers.notifications.nmj:Notifier',
])


def notify_download(ep_name):
    if sickbeard.CFG2['notifications']['download']:
        manager.map_method('notify_download', ep_name)


def notify_postprocess(ep_name):
    if sickbeard.CFG2['notifications']['process']:
        manager.map_method('notify_postprocess', ep_name)


def notify_subtitle_download(ep_name, lang):
    if sickbeard.CFG2['notifications']['subtitle']:
        manager.map_method('notify_subtitle_download', ep_name, lang)


def notify_snatch(ep_name):
    if sickbeard.CFG2['notifications']['snatch']:
        manager.map_method('notify_snatch', ep_name)


def notify_git_update(new_version=""):
    if sickbeard.CFG2['notifications']['update']:
        manager.map_method('notify_git_update', new_version)


def notify_login(ipaddress):
    if sickbeard.CFG2['notifications']['login'] and not sickbeard.helpers.is_ip_local(ipaddress):
        manager.map_method('notify_login', ipaddress)


def update_library(item):
    manager.map_method('update_library', item)


def get_config(provider: str, key: str = ''):
    result = manager[provider].plugin()._config
    if key:
        result = result[key]
    return result


def set_config(provider: str, key: str, value):
    import re
    if re.match(r'pass|api_?key|token', key):
        value = unhide(get_config(provider, key), value)
    get_config(provider)[key] = value


