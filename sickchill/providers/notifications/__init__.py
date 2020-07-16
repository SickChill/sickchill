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

notifiers = RegistrableExtensionManager('sickbeard.notifiers', [
    'plex = sickbeard.notifiers.plex:Notifier',
    'synoindex = sickbeard.notifiers.synoindex:Notifier',
    'telegram = sickbeard.notifiers.telegram:Notifier',
    'trakt = sickbeard.notifiers.trakt:Notifier',
    'join = sickbeard.notifiers.join:Notifier',
    'growl = sickbeard.notifiers.growl:Notifier',
    'emby = sickbeard.notifiers.emby:Notifier',
    'pushbullet = sickbeard.notifiers.pushbullet:Notifier',
    'nmjv2 = sickbeard.notifiers.nmjv2:Notifier',
    'tweet = sickbeard.notifiers.tweet:Notifier',
    'growl = sickbeard.notifiers.growl:Notifier',
    'pushalot = sickbeard.notifiers.pushalot:Notifier',
    'emailnotify = sickbeard.notifiers.emailnotify:Notifier',
    'prowl = sickbeard.notifiers.prowl:Notifier',
    'boxcar2 = sickbeard.notifiers.boxcar2:Notifier',
    'pytivo = sickbeard.notifiers.pytivo:Notifier',
    'boxcar2 = sickbeard.notifiers.boxcar2:Notifier',
    'nmj = sickbeard.notifiers.nmj:Notifier',
    'synologynotifier = sickbeard.notifiers.synologynotifier:Notifier',
    'matrix = sickbeard.notifiers.matrix:Notifier',
    'rocketchat = sickbeard.notifiers.rocketchat:Notifier',
    'trakt = sickbeard.notifiers.trakt:Notifier',
    'libnotify = sickbeard.notifiers.libnotify:Notifier',
    'rocketchat = sickbeard.notifiers.rocketchat:Notifier',
    'discord = sickbeard.notifiers.discord:Notifier',
    'pushbullet = sickbeard.notifiers.pushbullet:Notifier',
    'twilio_notify = sickbeard.notifiers.twilio_notify:Notifier',
    'tweet = sickbeard.notifiers.tweet:Notifier',
    'synologynotifier = sickbeard.notifiers.synologynotifier:Notifier',
    'plex = sickbeard.notifiers.plex:Notifier',
    'twilio_notify = sickbeard.notifiers.twilio_notify:Notifier',
    'discord = sickbeard.notifiers.discord:Notifier',
    'freemobile = sickbeard.notifiers.freemobile:Notifier',
    'slack = sickbeard.notifiers.slack:Notifier',
    'matrix = sickbeard.notifiers.matrix:Notifier',
    'synoindex = sickbeard.notifiers.synoindex:Notifier',
    'kodi = sickbeard.notifiers.kodi:Notifier',
    'nmjv2 = sickbeard.notifiers.nmjv2:Notifier',
    'emailnotify = sickbeard.notifiers.emailnotify:Notifier',
    'kodi = sickbeard.notifiers.kodi:Notifier',
    'pushalot = sickbeard.notifiers.pushalot:Notifier',
    'prowl = sickbeard.notifiers.prowl:Notifier',
    'pushover = sickbeard.notifiers.pushover:Notifier',
    'telegram = sickbeard.notifiers.telegram:Notifier',
    'pytivo = sickbeard.notifiers.pytivo:Notifier',
    'join = sickbeard.notifiers.join:Notifier',
    'pushover = sickbeard.notifiers.pushover:Notifier',
    'base = sickbeard.notifiers.base:Notifier',
    'emby = sickbeard.notifiers.emby:Notifier',
    'slack = sickbeard.notifiers.slack:Notifier',
    'freemobile = sickbeard.notifiers.freemobile:Notifier',
    'libnotify = sickbeard.notifiers.libnotify:Notifier',
    'nmj = sickbeard.notifiers.nmj:Notifier',
])
