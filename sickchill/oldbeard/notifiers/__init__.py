from sickchill import settings
from sickchill.oldbeard import helpers
from sickchill.oldbeard.notifiers import (  # twilio_notify,
    boxcar2,
    discord,
    emailnotify,
    emby,
    freemobile,
    growl,
    join,
    kodi,
    libnotify,
    matrix,
    nmj,
    nmjv2,
    plex,
    prowl,
    pushalot,
    pushbullet,
    pushover,
    pytivo,
    rocketchat,
    slack,
    synoindex,
    synologynotifier,
    telegram,
    trakt,
    tweet,
)

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
pushalot_notifier = pushalot.Notifier()
pushbullet_notifier = pushbullet.Notifier()
freemobile_notifier = freemobile.Notifier()
telegram_notifier = telegram.Notifier()
join_notifier = join.Notifier()
# social
twitter_notifier = tweet.Notifier()
# twilio_notifier = twilio_notify.Notifier()
trakt_notifier = trakt.Notifier()
email_notifier = emailnotify.Notifier()
slack_notifier = slack.Notifier()
rocketchat_notifier = rocketchat.Notifier()
matrix_notifier = matrix.Notifier()
discord_notifier = discord.Notifier()

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
    prowl_notifier,
    pushover_notifier,
    boxcar2_notifier,
    pushalot_notifier,
    pushbullet_notifier,
    twitter_notifier,
    # twilio_notifier,
    trakt_notifier,
    email_notifier,
    slack_notifier,
    rocketchat_notifier,
    matrix_notifier,
    discord_notifier,
    join_notifier,
]


def notify_download(ep_name):
    for n in notifiers:
        n.notify_download(ep_name)


def notify_postprocess(ep_name):
    for n in notifiers:
        n.notify_postprocess(ep_name)


def notify_subtitle_download(ep_name, lang):
    for n in notifiers:
        n.notify_subtitle_download(ep_name, lang)


def notify_snatch(ep_name):
    for n in notifiers:
        n.notify_snatch(ep_name)


def notify_git_update(new_version=""):
    if settings.NOTIFY_ON_UPDATE:
        for n in notifiers:
            if hasattr(n, "notify_git_update"):
                n.notify_git_update(new_version)
            else:
                print(n.__module__)


def notify_login(ipaddress):
    if settings.NOTIFY_ON_LOGIN and not helpers.is_ip_local(ipaddress):
        for n in notifiers:
            if hasattr(n, "notify_login"):
                n.notify_login(ipaddress)
            else:
                print(n.__module__)
