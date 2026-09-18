from sickchill import logger, settings
from sickchill.oldbeard import helpers
from sickchill.oldbeard.notifiers import (  # twilio_notify,
    discord,
    emailnotify,
    emby,
    freemobile,
    gotify,
    jellyfin,
    join,
    kodi,
    libnotify,
    matrix,
    mattermost,
    mattermostbot,
    nmj,
    nmjv2,
    plex,
    prowl,
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
from sickchill.plugins.api import PluginKind

# home theater / nas
kodi_notifier = kodi.Notifier()
plex_notifier = plex.Notifier()
emby_notifier = emby.Notifier()
jellyfin_notifier = jellyfin.Notifier()
nmj_notifier = nmj.Notifier()
nmjv2_notifier = nmjv2.Notifier()
synoindex_notifier = synoindex.Notifier()
synology_notifier = synologynotifier.Notifier()
pytivo_notifier = pytivo.Notifier()

# devices
prowl_notifier = prowl.Notifier()
libnotify_notifier = libnotify.Notifier()
pushover_notifier = pushover.Notifier()
pushbullet_notifier = pushbullet.Notifier()
freemobile_notifier = freemobile.Notifier()
telegram_notifier = telegram.Notifier()
join_notifier = join.Notifier()
gotify_notifier = gotify.Notifier()

# social
twitter_notifier = tweet.Notifier()
# twilio_notifier = twilio_notify.Notifier()
trakt_notifier = trakt.Notifier()
email_notifier = emailnotify.Notifier()
slack_notifier = slack.Notifier()
mattermost_notifier = mattermost.Notifier()
mattermostbot_notifier = mattermostbot.Notifier()
rocketchat_notifier = rocketchat.Notifier()
matrix_notifier = matrix.Notifier()
# Kept for UI testDiscord shim; Discord delivery is via NotifierPlugin.
discord_notifier = discord.Notifier()

# Broadcast list empty: all notifiers delivered via plugin_manager.enabled(NOTIFIER).
# Module-level *_notifier instances remain for update_library / UI tests.
notifiers = []


def _broadcast_plugins(method_name, *args, **kwargs):
    try:
        from sickchill.plugins.manager import plugin_manager

        for plugin in plugin_manager.enabled(PluginKind.NOTIFIER):
            method = getattr(plugin, method_name, None)
            if not callable(method):
                continue
            try:
                method(*args, **kwargs)
            except Exception as error:
                logger.exception(f"Plugin notifier {plugin.id} {method_name} failed: {error}")
    except Exception as error:
        logger.debug(f"Plugin notifier broadcast skipped: {error}")


def notify_download(ep_name):
    for n in notifiers:
        n.notify_download(ep_name)
    _broadcast_plugins("notify_download", ep_name)


def notify_postprocess(ep_name):
    for n in notifiers:
        n.notify_postprocess(ep_name)
    _broadcast_plugins("notify_postprocess", ep_name)


def notify_subtitle_download(ep_name, lang):
    for n in notifiers:
        n.notify_subtitle_download(ep_name, lang)
    _broadcast_plugins("notify_subtitle_download", ep_name, lang)


def notify_snatch(ep_name):
    for n in notifiers:
        n.notify_snatch(ep_name)
    _broadcast_plugins("notify_snatch", ep_name)


def notify_update(new_version=""):
    if settings.NOTIFY_ON_UPDATE:
        for n in notifiers:
            if hasattr(n, "notify_update"):
                n.notify_update(new_version)
            else:
                print(n.__module__)
        _broadcast_plugins("notify_update", new_version)


def notify_login(ipaddress):
    if settings.NOTIFY_ON_LOGIN and not helpers.is_ip_local(ipaddress):
        for n in notifiers:
            if hasattr(n, "notify_login"):
                n.notify_login(ipaddress)
            else:
                print(n.__module__)
        _broadcast_plugins("notify_login", ipaddress)


def notify_logged_error(ui_error):
    if settings.NOTIFY_ON_LOGGED_ERROR:
        for n in notifiers:
            if hasattr(n, "notify_logged_error"):
                n.notify_logged_error(ui_error)
        _broadcast_plugins("notify_logged_error", ui_error)
