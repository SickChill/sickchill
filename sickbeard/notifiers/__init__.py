# coding=utf-8

# Author: Dustyn Gibson <miigotu@gmail.com>
# URL: https://sickrage.github.io
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

import sickbeard

from sickbeard.notifiers import kodi, plex, emby, nmj, nmjv2, synoindex, \
    synologynotifier, pytivo, growl, prowl, libnotify, pushover, boxcar2, \
    nma, pushalot, pushbullet, freemobile, telegram, tweet, trakt, emailnotify, \
    slack, join, twilio_notify

# home theater / nas
kodi_notifier = kodi.Notifier()
plex_notifier = plex.Notifier()
emby_notifier = emby.Notifier()
nmj_notifier = nmj.Notifier()
nmjv2_notifier = nmjv2.Notifier()
synoindex_notifier = synoindex.Notifier()
synology_notifier = synologynotifier.Notifier()
pytivo_notifier = pytivo.Notifier()

# devices
growl_notifier = growl.Notifier()
prowl_notifier = prowl.Notifier()
libnotify_notifier = libnotify.Notifier()
pushover_notifier = pushover.Notifier()
boxcar2_notifier = boxcar2.Notifier()
nma_notifier = nma.Notifier()
pushalot_notifier = pushalot.Notifier()
pushbullet_notifier = pushbullet.Notifier()
freemobile_notifier = freemobile.Notifier()
telegram_notifier = telegram.Notifier()
genericurl_notifier = genericurl.Notifier()
join_notifier = join.Notifier()
# social
twitter_notifier = tweet.Notifier()
twilio_notifier = twilio_notify.Notifier()
trakt_notifier = trakt.Notifier()
email_notifier = emailnotify.Notifier()
slack_notifier = slack.Notifier()

notifiers = [
    libnotify_notifier,  # Libnotify notifier goes first because it doesn't involve blocking on network activity.
    kodi_notifier,
    plex_notifier,
    nmj_notifier,
    nmjv2_notifier,
    synoindex_notifier,
    synology_notifier,
    pytivo_notifier,
    growl_notifier,
    freemobile_notifier,
    telegram_notifier,
    genericurl_notifier,
    prowl_notifier,
    pushover_notifier,
    boxcar2_notifier,
    nma_notifier,
    pushalot_notifier,
    pushbullet_notifier,
    twitter_notifier,
    twilio_notifier,
    trakt_notifier,
    email_notifier,
    slack_notifier,
    join_notifier,
]


def notify_download(ep_name):
    for n in notifiers:
        n.notify_download(ep_name)


def notify_subtitle_download(ep_name, lang):
    for n in notifiers:
        n.notify_subtitle_download(ep_name, lang)


def notify_snatch(ep_name):
    for n in notifiers:
        n.notify_snatch(ep_name)


def notify_git_update(new_version=""):
    for n in notifiers:
        if sickbeard.NOTIFY_ON_UPDATE:
            n.notify_git_update(new_version)


def notify_login(ipaddress):
    for n in notifiers:
        if sickbeard.NOTIFY_ON_LOGIN and hasattr(n, 'notify_login'):
            n.notify_login(ipaddress)
        else:
            print(n.__module__)

