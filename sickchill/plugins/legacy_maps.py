from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LegacyField:
    name: str  # key under [NOTIFIERS][[id]] (notifiers) or [extensions][[kind]][[[id]]]
    settings_attr: str  # attribute on sickchill.settings
    legacy_keys: tuple[str, ...] = ()
    type: str = "str"  # str|bool|int


@dataclass(frozen=True)
class LegacyMap:
    kind: str  # notifiers|clients|providers|metadata
    plugin_id: str
    legacy_section: str
    fields: tuple[LegacyField, ...] = ()
    # False when the INI section is shared with non-notifier settings (e.g. Synology DSM).
    delete_section: bool = True


# Notifier LegacyMap fields persist under top-level [NOTIFIERS][[plugin_id]], not [extensions].


DISCORD_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="discord",
    legacy_section="Discord",
    fields=(
        LegacyField("enabled", "USE_DISCORD", ("use_discord",), "bool"),
        LegacyField("webhook", "DISCORD_WEBHOOK", ("discord_webhook",), "str"),
        LegacyField("bot_name", "DISCORD_NAME", ("discord_name",), "str"),
        LegacyField("avatar_url", "DISCORD_AVATAR_URL", ("discord_avatar_url",), "str"),
        LegacyField("tts", "DISCORD_TTS", ("discord_tts",), "bool"),
        LegacyField("notify_snatch", "DISCORD_NOTIFY_SNATCH", ("discord_notify_snatch",), "bool"),
        LegacyField("notify_download", "DISCORD_NOTIFY_DOWNLOAD", ("discord_notify_download",), "bool"),
        LegacyField("notify_subtitle_download", "DISCORD_NOTIFY_SUBTITLEDOWNLOAD", ("discord_notify_subtitledownload",), "bool"),
    ),
)

KODI_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="kodi",
    legacy_section="KODI",
    fields=(
        LegacyField("enabled", "USE_KODI", ("use_kodi",), "bool"),
        LegacyField("always_on", "KODI_ALWAYS_ON", ("kodi_always_on",), "bool"),
        LegacyField("notify_onsnatch", "KODI_NOTIFY_ONSNATCH", ("kodi_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "KODI_NOTIFY_ONDOWNLOAD", ("kodi_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "KODI_NOTIFY_ONSUBTITLEDOWNLOAD", ("kodi_notify_onsubtitledownload",), "bool"),
        LegacyField("update_library", "KODI_UPDATE_LIBRARY", ("kodi_update_library",), "bool"),
        LegacyField("update_full", "KODI_UPDATE_FULL", ("kodi_update_full",), "bool"),
        LegacyField("update_onlyfirst", "KODI_UPDATE_ONLYFIRST", ("kodi_update_onlyfirst",), "bool"),
        LegacyField("host", "KODI_HOST", ("kodi_host",), "str"),
        LegacyField("username", "KODI_USERNAME", ("kodi_username",), "str"),
        LegacyField("password", "KODI_PASSWORD", ("kodi_password",), "str"),
    ),
)

PLEX_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="plex",
    legacy_section="Plex",
    fields=(
        LegacyField("use_plex_server", "USE_PLEX_SERVER", ("use_plex_server",), "bool"),
        LegacyField("notify_onsnatch", "PLEX_NOTIFY_ONSNATCH", ("plex_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "PLEX_NOTIFY_ONDOWNLOAD", ("plex_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "PLEX_NOTIFY_ONSUBTITLEDOWNLOAD", ("plex_notify_onsubtitledownload",), "bool"),
        LegacyField("update_library", "PLEX_UPDATE_LIBRARY", ("plex_update_library",), "bool"),
        LegacyField("server_host", "PLEX_SERVER_HOST", ("plex_server_host",), "str"),
        LegacyField("server_token", "PLEX_SERVER_TOKEN", ("plex_server_token",), "str"),
        LegacyField("client_host", "PLEX_CLIENT_HOST", ("plex_client_host",), "str"),
        LegacyField("server_username", "PLEX_SERVER_USERNAME", ("plex_server_username",), "str"),
        LegacyField("server_password", "PLEX_SERVER_PASSWORD", ("plex_server_password",), "str"),
        LegacyField("use_plex_client", "USE_PLEX_CLIENT", ("use_plex_client",), "bool"),
        LegacyField("client_username", "PLEX_CLIENT_USERNAME", ("plex_client_username",), "str"),
        LegacyField("client_password", "PLEX_CLIENT_PASSWORD", ("plex_client_password",), "str"),
        LegacyField("server_https", "PLEX_SERVER_HTTPS", ("plex_server_https",), "bool"),
    ),
)

EMBY_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="emby",
    legacy_section="Emby",
    fields=(
        LegacyField("enabled", "USE_EMBY", ("use_emby",), "bool"),
        LegacyField("host", "EMBY_HOST", ("emby_host",), "str"),
        LegacyField("apikey", "EMBY_APIKEY", ("emby_apikey",), "str"),
    ),
)

JELLYFIN_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="jellyfin",
    legacy_section="Jellyfin",
    fields=(
        LegacyField("enabled", "USE_JELLYFIN", ("use_jellyfin",), "bool"),
        LegacyField("host", "JELLYFIN_HOST", ("jellyfin_host",), "str"),
        LegacyField("apikey", "JELLYFIN_APIKEY", ("jellyfin_apikey",), "str"),
    ),
)

PROWL_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="prowl",
    legacy_section="Prowl",
    fields=(
        LegacyField("enabled", "USE_PROWL", ("use_prowl",), "bool"),
        LegacyField("notify_onsnatch", "PROWL_NOTIFY_ONSNATCH", ("prowl_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "PROWL_NOTIFY_ONDOWNLOAD", ("prowl_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "PROWL_NOTIFY_ONSUBTITLEDOWNLOAD", ("prowl_notify_onsubtitledownload",), "bool"),
        LegacyField("api", "PROWL_API", ("prowl_api",), "str"),
        LegacyField("priority", "PROWL_PRIORITY", ("prowl_priority",), "str"),
        LegacyField("message_title", "PROWL_MESSAGE_TITLE", ("prowl_message_title",), "str"),
    ),
)

TWITTER_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="twitter",
    legacy_section="Twitter",
    fields=(
        LegacyField("enabled", "USE_TWITTER", ("use_twitter",), "bool"),
        LegacyField("notify_onsnatch", "TWITTER_NOTIFY_ONSNATCH", ("twitter_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "TWITTER_NOTIFY_ONDOWNLOAD", ("twitter_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD", ("twitter_notify_onsubtitledownload",), "bool"),
        LegacyField("username", "TWITTER_USERNAME", ("twitter_username",), "str"),
        LegacyField("password", "TWITTER_PASSWORD", ("twitter_password",), "str"),
        LegacyField("prefix", "TWITTER_PREFIX", ("twitter_prefix",), "str"),
        LegacyField("dmto", "TWITTER_DMTO", ("twitter_dmto",), "str"),
        LegacyField("usedm", "TWITTER_USEDM", ("twitter_usedm",), "bool"),
    ),
)

TWILIO_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="twilio",
    legacy_section="Twilio",
    fields=(
        LegacyField("enabled", "USE_TWILIO", ("use_twilio",), "bool"),
        LegacyField("notify_onsnatch", "TWILIO_NOTIFY_ONSNATCH", ("twilio_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "TWILIO_NOTIFY_ONDOWNLOAD", ("twilio_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "TWILIO_NOTIFY_ONSUBTITLEDOWNLOAD", ("twilio_notify_onsubtitledownload",), "bool"),
        LegacyField("phone_sid", "TWILIO_PHONE_SID", ("twilio_phone_sid",), "str"),
        LegacyField("account_sid", "TWILIO_ACCOUNT_SID", ("twilio_account_sid",), "str"),
        LegacyField("auth_token", "TWILIO_AUTH_TOKEN", ("twilio_auth_token",), "str"),
        LegacyField("to_number", "TWILIO_TO_NUMBER", ("twilio_to_number",), "str"),
    ),
)

NMJ_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="nmj",
    legacy_section="NMJ",
    fields=(
        LegacyField("enabled", "USE_NMJ", ("use_nmj",), "bool"),
        LegacyField("host", "NMJ_HOST", ("nmj_host",), "str"),
        LegacyField("database", "NMJ_DATABASE", ("nmj_database",), "str"),
        LegacyField("mount", "NMJ_MOUNT", ("nmj_mount",), "str"),
    ),
)

NMJV2_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="nmjv2",
    legacy_section="NMJv2",
    fields=(
        LegacyField("enabled", "USE_NMJv2", ("use_nmjv2",), "bool"),
        LegacyField("host", "NMJv2_HOST", ("nmjv2_host",), "str"),
        LegacyField("database", "NMJv2_DATABASE", ("nmjv2_database",), "str"),
        LegacyField("dbloc", "NMJv2_DBLOC", ("nmjv2_dbloc",), "str"),
    ),
)

SYNOLOGYNOTIFIER_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="synologynotifier",
    legacy_section="SynologyNotifier",
    fields=(
        LegacyField("enabled", "USE_SYNOLOGYNOTIFIER", ("use_synologynotifier",), "bool"),
        LegacyField("notify_onsnatch", "SYNOLOGYNOTIFIER_NOTIFY_ONSNATCH", ("synologynotifier_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "SYNOLOGYNOTIFIER_NOTIFY_ONDOWNLOAD", ("synologynotifier_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "SYNOLOGYNOTIFIER_NOTIFY_ONSUBTITLEDOWNLOAD", ("synologynotifier_notify_onsubtitledownload",), "bool"),
    ),
)

PYTIVO_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="pytivo",
    legacy_section="pyTivo",
    fields=(
        LegacyField("enabled", "USE_PYTIVO", ("use_pytivo",), "bool"),
        LegacyField("notify_onsnatch", "PYTIVO_NOTIFY_ONSNATCH", ("pytivo_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "PYTIVO_NOTIFY_ONDOWNLOAD", ("pytivo_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "PYTIVO_NOTIFY_ONSUBTITLEDOWNLOAD", ("pytivo_notify_onsubtitledownload",), "bool"),
        LegacyField("host", "PYTIVO_HOST", ("pytivo_host",), "str"),
        LegacyField("share_name", "PYTIVO_SHARE_NAME", ("pytivo_share_name",), "str"),
        LegacyField("tivo_name", "PYTIVO_TIVO_NAME", ("pytivo_tivo_name",), "str"),
    ),
)

PUSHBULLET_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="pushbullet",
    legacy_section="Pushbullet",
    fields=(
        LegacyField("enabled", "USE_PUSHBULLET", ("use_pushbullet",), "bool"),
        LegacyField("notify_onsnatch", "PUSHBULLET_NOTIFY_ONSNATCH", ("pushbullet_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "PUSHBULLET_NOTIFY_ONDOWNLOAD", ("pushbullet_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "PUSHBULLET_NOTIFY_ONSUBTITLEDOWNLOAD", ("pushbullet_notify_onsubtitledownload",), "bool"),
        LegacyField("api", "PUSHBULLET_API", ("pushbullet_api",), "str"),
        LegacyField("device", "PUSHBULLET_DEVICE", ("pushbullet_device",), "str"),
        LegacyField("channel", "PUSHBULLET_CHANNEL", ("pushbullet_channel",), "str"),
    ),
)

SLACK_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="slack",
    legacy_section="Slack",
    fields=(
        LegacyField("enabled", "USE_SLACK", ("use_slack",), "bool"),
        LegacyField("notify_snatch", "SLACK_NOTIFY_SNATCH", ("slack_notify_snatch",), "bool"),
        LegacyField("notify_download", "SLACK_NOTIFY_DOWNLOAD", ("slack_notify_download",), "bool"),
        LegacyField("notify_subtitledownload", "SLACK_NOTIFY_SUBTITLEDOWNLOAD", ("slack_notify_subtitledownload",), "bool"),
        LegacyField("webhook", "SLACK_WEBHOOK", ("slack_webhook",), "str"),
        LegacyField("icon_emoji", "SLACK_ICON_EMOJI", ("slack_icon_emoji",), "str"),
    ),
)

ROCKETCHAT_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="rocketchat",
    legacy_section="RocketChat",
    fields=(
        LegacyField("enabled", "USE_ROCKETCHAT", ("use_rocketchat",), "bool"),
        LegacyField("notify_snatch", "ROCKETCHAT_NOTIFY_SNATCH", ("rocketchat_notify_snatch",), "bool"),
        LegacyField("notify_download", "ROCKETCHAT_NOTIFY_DOWNLOAD", ("rocketchat_notify_download",), "bool"),
        LegacyField("notify_subtitledownload", "ROCKETCHAT_NOTIFY_SUBTITLEDOWNLOAD", ("rocketchat_notify_subtitledownload",), "bool"),
        LegacyField("webhook", "ROCKETCHAT_WEBHOOK", ("rocketchat_webhook",), "str"),
        LegacyField("icon_emoji", "ROCKETCHAT_ICON_EMOJI", ("rocketchat_icon_emoji",), "str"),
    ),
)

MATRIX_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="matrix",
    legacy_section="Matrix",
    fields=(
        LegacyField("enabled", "USE_MATRIX", ("use_matrix",), "bool"),
        LegacyField("notify_snatch", "MATRIX_NOTIFY_SNATCH", ("matrix_notify_snatch",), "bool"),
        LegacyField("notify_download", "MATRIX_NOTIFY_DOWNLOAD", ("matrix_notify_download",), "bool"),
        LegacyField("notify_subtitledownload", "MATRIX_NOTIFY_SUBTITLEDOWNLOAD", ("matrix_notify_subtitledownload",), "bool"),
        LegacyField("api_token", "MATRIX_API_TOKEN", ("matrix_api_token",), "str"),
        LegacyField("server", "MATRIX_SERVER", ("matrix_server",), "str"),
        LegacyField("room", "MATRIX_ROOM", ("matrix_room",), "str"),
    ),
)

MATTERMOST_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="mattermost",
    legacy_section="Mattermost",
    fields=(
        LegacyField("enabled", "USE_MATTERMOST", ("use_mattermost",), "bool"),
        LegacyField("notify_snatch", "MATTERMOST_NOTIFY_SNATCH", ("mattermost_notify_snatch",), "bool"),
        LegacyField("notify_download", "MATTERMOST_NOTIFY_DOWNLOAD", ("mattermost_notify_download",), "bool"),
        LegacyField("notify_subtitledownload", "MATTERMOST_NOTIFY_SUBTITLEDOWNLOAD", ("mattermost_notify_subtitledownload",), "bool"),
        LegacyField("username", "MATTERMOST_USERNAME", ("mattermost_username",), "str"),
        LegacyField("webhook", "MATTERMOST_WEBHOOK", ("mattermost_webhook",), "str"),
        LegacyField("icon_emoji", "MATTERMOST_ICON_EMOJI", ("mattermost_icon_emoji",), "str"),
    ),
)

MATTERMOSTBOT_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="mattermostbot",
    legacy_section="MattermostBot",
    fields=(
        LegacyField("enabled", "USE_MATTERMOSTBOT", ("use_mattermostbot",), "bool"),
        LegacyField("notify_snatch", "MATTERMOSTBOT_NOTIFY_SNATCH", ("mattermostbot_notify_snatch",), "bool"),
        LegacyField("notify_download", "MATTERMOSTBOT_NOTIFY_DOWNLOAD", ("mattermostbot_notify_download",), "bool"),
        LegacyField("notify_subtitledownload", "MATTERMOSTBOT_NOTIFY_SUBTITLEDOWNLOAD", ("mattermostbot_notify_subtitledownload",), "bool"),
        LegacyField("token", "MATTERMOSTBOT_TOKEN", ("mattermostbot_token",), "str"),
        LegacyField("channel", "MATTERMOSTBOT_CHANNEL", ("mattermostbot_channel",), "str"),
        LegacyField("url", "MATTERMOSTBOT_URL", ("mattermostbot_url",), "str"),
        LegacyField("icon_emoji", "MATTERMOSTBOT_ICON_EMOJI", ("mattermostbot_icon_emoji",), "str"),
        LegacyField("author", "MATTERMOSTBOT_AUTHOR", ("mattermostbot_author",), "str"),
    ),
)

GOTIFY_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="gotify",
    legacy_section="Gotify",
    fields=(
        LegacyField("enabled", "USE_GOTIFY", ("use_gotify",), "bool"),
        LegacyField("notify_onsnatch", "GOTIFY_NOTIFY_ONSNATCH", ("gotify_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "GOTIFY_NOTIFY_ONDOWNLOAD", ("gotify_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "GOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD", ("gotify_notify_onsubtitledownload",), "bool"),
        LegacyField("host", "GOTIFY_HOST", ("gotify_host",), "str"),
        LegacyField("authorizationtoken", "GOTIFY_AUTHORIZATIONTOKEN", ("gotify_authorizationtoken",), "str"),
    ),
)

JOIN_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="join",
    legacy_section="Join",
    fields=(
        LegacyField("enabled", "USE_JOIN", ("use_join",), "bool"),
        LegacyField("notify_onsnatch", "JOIN_NOTIFY_ONSNATCH", ("join_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "JOIN_NOTIFY_ONDOWNLOAD", ("join_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "JOIN_NOTIFY_ONSUBTITLEDOWNLOAD", ("join_notify_onsubtitledownload",), "bool"),
        LegacyField("id", "JOIN_ID", ("join_id",), "str"),
        LegacyField("apikey", "JOIN_APIKEY", ("join_apikey",), "str"),
    ),
)

FREEMOBILE_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="freemobile",
    legacy_section="FreeMobile",
    fields=(
        LegacyField("enabled", "USE_FREEMOBILE", ("use_freemobile",), "bool"),
        LegacyField("notify_onsnatch", "FREEMOBILE_NOTIFY_ONSNATCH", ("freemobile_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "FREEMOBILE_NOTIFY_ONDOWNLOAD", ("freemobile_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD", ("freemobile_notify_onsubtitledownload",), "bool"),
        LegacyField("id", "FREEMOBILE_ID", ("freemobile_id",), "str"),
        LegacyField("apikey", "FREEMOBILE_APIKEY", ("freemobile_apikey",), "str"),
    ),
)

TELEGRAM_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="telegram",
    legacy_section="Telegram",
    fields=(
        LegacyField("enabled", "USE_TELEGRAM", ("use_telegram",), "bool"),
        LegacyField("notify_onsnatch", "TELEGRAM_NOTIFY_ONSNATCH", ("telegram_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "TELEGRAM_NOTIFY_ONDOWNLOAD", ("telegram_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "TELEGRAM_NOTIFY_ONSUBTITLEDOWNLOAD", ("telegram_notify_onsubtitledownload",), "bool"),
        LegacyField("id", "TELEGRAM_ID", ("telegram_id",), "str"),
        LegacyField("apikey", "TELEGRAM_APIKEY", ("telegram_apikey",), "str"),
    ),
)

EMAIL_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="email",
    legacy_section="Email",
    fields=(
        LegacyField("enabled", "USE_EMAIL", ("use_email",), "bool"),
        LegacyField("notify_onsnatch", "EMAIL_NOTIFY_ONSNATCH", ("email_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "EMAIL_NOTIFY_ONDOWNLOAD", ("email_notify_ondownload",), "bool"),
        LegacyField("notify_onpostprocess", "EMAIL_NOTIFY_ONPOSTPROCESS", ("email_notify_onpostprocess",), "bool"),
        LegacyField("notify_onsubtitledownload", "EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD", ("email_notify_onsubtitledownload",), "bool"),
        LegacyField("host", "EMAIL_HOST", ("email_host",), "str"),
        LegacyField("port", "EMAIL_PORT", ("email_port",), "int"),
        LegacyField("tls", "EMAIL_TLS", ("email_tls",), "bool"),
        LegacyField("user", "EMAIL_USER", ("email_user",), "str"),
        LegacyField("password", "EMAIL_PASSWORD", ("email_password",), "str"),
        LegacyField("from", "EMAIL_FROM", ("email_from",), "str"),
        LegacyField("list", "EMAIL_LIST", ("email_list",), "str"),
        LegacyField("subject", "EMAIL_SUBJECT", ("email_subject",), "str"),
    ),
)

TRAKT_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="trakt",
    legacy_section="Trakt",
    fields=(
        LegacyField("enabled", "USE_TRAKT", ("use_trakt",), "bool"),
        LegacyField("username", "TRAKT_USERNAME", ("trakt_username",), "str"),
        LegacyField("api_key", "TRAKT_API_KEY", ("trakt_api_key",), "str"),
        LegacyField("api_secret", "TRAKT_API_SECRET", ("trakt_api_secret",), "str"),
        LegacyField("access_token", "TRAKT_ACCESS_TOKEN", ("trakt_access_token",), "str"),
        LegacyField("refresh_token", "TRAKT_REFRESH_TOKEN", ("trakt_refresh_token",), "str"),
        LegacyField("remove_watchlist", "TRAKT_REMOVE_WATCHLIST", ("trakt_remove_watchlist",), "bool"),
        LegacyField("remove_serieslist", "TRAKT_REMOVE_SERIESLIST", ("trakt_remove_serieslist",), "bool"),
        LegacyField("remove_show_from_sickchill", "TRAKT_REMOVE_SHOW_FROM_SICKCHILL", ("trakt_remove_show_from_sickchill",), "bool"),
        LegacyField("sync_watchlist", "TRAKT_SYNC_WATCHLIST", ("trakt_sync_watchlist",), "bool"),
        LegacyField("method_add", "TRAKT_METHOD_ADD", ("trakt_method_add",), "int"),
        LegacyField("start_paused", "TRAKT_START_PAUSED", ("trakt_start_paused",), "bool"),
        LegacyField("use_recommended", "TRAKT_USE_RECOMMENDED", ("trakt_use_recommended",), "bool"),
        LegacyField("sync", "TRAKT_SYNC", ("trakt_sync",), "bool"),
        LegacyField("sync_remove", "TRAKT_SYNC_REMOVE", ("trakt_sync_remove",), "bool"),
        LegacyField("default_indexer", "TRAKT_DEFAULT_INDEXER", ("trakt_default_indexer",), "int"),
        LegacyField("timeout", "TRAKT_TIMEOUT", ("trakt_timeout",), "int"),
        LegacyField("blacklist_name", "TRAKT_BLACKLIST_NAME", ("trakt_blacklist_name",), "str"),
    ),
)

LIBNOTIFY_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="libnotify",
    legacy_section="Libnotify",
    fields=(
        LegacyField("enabled", "USE_LIBNOTIFY", ("use_libnotify",), "bool"),
        LegacyField("notify_onsnatch", "LIBNOTIFY_NOTIFY_ONSNATCH", ("libnotify_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "LIBNOTIFY_NOTIFY_ONDOWNLOAD", ("libnotify_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "LIBNOTIFY_NOTIFY_ONSUBTITLEDOWNLOAD", ("libnotify_notify_onsubtitledownload",), "bool"),
    ),
)

SYNOINDEX_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="synoindex",
    legacy_section="Synology",
    fields=(LegacyField("enabled", "USE_SYNOINDEX", ("use_synoindex",), "bool"),),
    delete_section=False,  # Synology section also holds DSM download-client keys
)


PUSHOVER_MAP = LegacyMap(
    kind="notifiers",
    plugin_id="pushover",
    legacy_section="Pushover",
    fields=(
        LegacyField("enabled", "USE_PUSHOVER", ("use_pushover",), "bool"),
        LegacyField("notify_onsnatch", "PUSHOVER_NOTIFY_ONSNATCH", ("pushover_notify_onsnatch",), "bool"),
        LegacyField("notify_ondownload", "PUSHOVER_NOTIFY_ONDOWNLOAD", ("pushover_notify_ondownload",), "bool"),
        LegacyField("notify_onsubtitledownload", "PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD", ("pushover_notify_onsubtitledownload",), "bool"),
        LegacyField("userkey", "PUSHOVER_USERKEY", ("pushover_userkey",), "str"),
        LegacyField("apikey", "PUSHOVER_APIKEY", ("pushover_apikey",), "str"),
        LegacyField("device", "PUSHOVER_DEVICE", ("pushover_device",), "str"),
        LegacyField("sound", "PUSHOVER_SOUND", ("pushover_sound",), "str"),
        LegacyField("priority", "PUSHOVER_PRIORITY", ("pushover_priority",), "str"),
    ),
)

NOTIFIER_LEGACY_MAPS: tuple[LegacyMap, ...] = (
    PUSHOVER_MAP,
    DISCORD_MAP,
    KODI_MAP,
    PLEX_MAP,
    EMBY_MAP,
    JELLYFIN_MAP,
    PROWL_MAP,
    TWITTER_MAP,
    TWILIO_MAP,
    NMJ_MAP,
    NMJV2_MAP,
    SYNOLOGYNOTIFIER_MAP,
    PYTIVO_MAP,
    PUSHBULLET_MAP,
    SLACK_MAP,
    ROCKETCHAT_MAP,
    MATRIX_MAP,
    MATTERMOST_MAP,
    MATTERMOSTBOT_MAP,
    GOTIFY_MAP,
    JOIN_MAP,
    FREEMOBILE_MAP,
    TELEGRAM_MAP,
    EMAIL_MAP,
    TRAKT_MAP,
    LIBNOTIFY_MAP,
    SYNOINDEX_MAP,
)

# ---------------------------------------------------------------------------
# Download clients → top-level [CLIENTS][[id]] (NOT [extensions])
# Migrated via migrate_client_maps(); do not add these to ALL_LEGACY_MAPS.
# ---------------------------------------------------------------------------

# download_station is seeded from [Synology] first, then [TORRENT] only fills empty keys
# (see CLIENT_SECTION_MAPS order) so DSM credentials win when both sections exist.
TORRENT_CLIENT_IDS: tuple[str, ...] = (
    "transmission",
    "utorrent",
    "deluge",
    "deluged",
    "qbittorrent",
    "rtorrent",
    "mlnet",
    "putio",
)

_TORRENT_SHARED_FIELDS: tuple[LegacyField, ...] = (
    LegacyField("host", "TORRENT_HOST", ("torrent_host",), "str"),
    LegacyField("username", "TORRENT_USERNAME", ("torrent_username",), "str"),
    LegacyField("password", "TORRENT_PASSWORD", ("torrent_password",), "str"),
    LegacyField("path", "TORRENT_PATH", ("torrent_path",), "str"),
    LegacyField("path_incomplete", "TORRENT_PATH_INCOMPLETE", ("torrent_path_incomplete",), "str"),
    LegacyField("label", "TORRENT_LABEL", ("torrent_label",), "str"),
    LegacyField("label_anime", "TORRENT_LABEL_ANIME", ("torrent_label_anime",), "str"),
    LegacyField("paused", "TORRENT_PAUSED", ("torrent_paused",), "bool"),
    LegacyField("seed_time", "TORRENT_SEED_TIME", ("torrent_seed_time",), "int"),
    LegacyField("verify_cert", "TORRENT_VERIFY_CERT", ("torrent_verify_cert",), "bool"),
)

_TRANSMISSION_EXTRA_FIELDS: tuple[LegacyField, ...] = (
    LegacyField("rpcurl", "TORRENT_RPCURL", ("torrent_rpcurl",), "str"),
    LegacyField("high_bandwidth", "TORRENT_HIGH_BANDWIDTH", ("torrent_high_bandwidth",), "bool"),
)

_RTORRENT_EXTRA_FIELDS: tuple[LegacyField, ...] = (LegacyField("auth_type", "TORRENT_AUTH_TYPE", ("torrent_auth_type",), "str"),)


def _torrent_client_map(plugin_id: str) -> LegacyMap:
    fields = _TORRENT_SHARED_FIELDS
    if plugin_id == "transmission":
        fields = _TORRENT_SHARED_FIELDS + _TRANSMISSION_EXTRA_FIELDS
    elif plugin_id == "rtorrent":
        fields = _TORRENT_SHARED_FIELDS + _RTORRENT_EXTRA_FIELDS
    return LegacyMap(
        kind="clients",
        plugin_id=plugin_id,
        legacy_section="TORRENT",
        fields=fields,
        delete_section=True,
    )


SABNZBD_CLIENT_MAP = LegacyMap(
    kind="clients",
    plugin_id="sabnzbd",
    legacy_section="SABnzbd",
    fields=(
        LegacyField("username", "SAB_USERNAME", ("sab_username",), "str"),
        LegacyField("password", "SAB_PASSWORD", ("sab_password",), "str"),
        LegacyField("apikey", "SAB_APIKEY", ("sab_apikey",), "str"),
        LegacyField("category", "SAB_CATEGORY", ("sab_category",), "str"),
        LegacyField("category_backlog", "SAB_CATEGORY_BACKLOG", ("sab_category_backlog",), "str"),
        LegacyField("category_anime", "SAB_CATEGORY_ANIME", ("sab_category_anime",), "str"),
        LegacyField("category_anime_backlog", "SAB_CATEGORY_ANIME_BACKLOG", ("sab_category_anime_backlog",), "str"),
        LegacyField("host", "SAB_HOST", ("sab_host",), "str"),
        LegacyField("forced", "SAB_FORCED", ("sab_forced",), "bool"),
    ),
)

NZBGET_CLIENT_MAP = LegacyMap(
    kind="clients",
    plugin_id="nzbget",
    legacy_section="NZBget",  # legacy spelling
    fields=(
        LegacyField("username", "NZBGET_USERNAME", ("nzbget_username",), "str"),
        LegacyField("password", "NZBGET_PASSWORD", ("nzbget_password",), "str"),
        LegacyField("category", "NZBGET_CATEGORY", ("nzbget_category",), "str"),
        LegacyField("category_backlog", "NZBGET_CATEGORY_BACKLOG", ("nzbget_category_backlog",), "str"),
        LegacyField("category_anime", "NZBGET_CATEGORY_ANIME", ("nzbget_category_anime",), "str"),
        LegacyField("category_anime_backlog", "NZBGET_CATEGORY_ANIME_BACKLOG", ("nzbget_category_anime_backlog",), "str"),
        LegacyField("host", "NZBGET_HOST", ("nzbget_host",), "str"),
        LegacyField("use_https", "NZBGET_USE_HTTPS", ("nzbget_use_https",), "bool"),
        LegacyField("priority", "NZBGET_PRIORITY", ("nzbget_priority",), "int"),
    ),
)

BLACKHOLE_CLIENT_MAP = LegacyMap(
    kind="clients",
    plugin_id="blackhole",
    legacy_section="Blackhole",
    fields=(
        LegacyField("nzb_dir", "NZB_DIR", ("nzb_dir",), "str"),
        LegacyField("torrent_dir", "TORRENT_DIR", ("torrent_dir",), "str"),
    ),
)

# Shared [Synology] section: DSM download-client keys only; leave use_synoindex for notifier map.
DOWNLOAD_STATION_SYNOLOGY_MAP = LegacyMap(
    kind="clients",
    plugin_id="download_station",
    legacy_section="Synology",
    fields=(
        LegacyField("host", "SYNOLOGY_DSM_HOST", ("host",), "str"),
        LegacyField("username", "SYNOLOGY_DSM_USERNAME", ("username",), "str"),
        LegacyField("password", "SYNOLOGY_DSM_PASSWORD", ("password",), "str"),
        LegacyField("path", "SYNOLOGY_DSM_PATH", ("path",), "str"),
    ),
    delete_section=False,
)

CLIENT_SECTION_MAPS: tuple[LegacyMap, ...] = tuple(_torrent_client_map(cid) for cid in TORRENT_CLIENT_IDS) + (
    SABNZBD_CLIENT_MAP,
    NZBGET_CLIENT_MAP,
    BLACKHOLE_CLIENT_MAP,
    DOWNLOAD_STATION_SYNOLOGY_MAP,
    # After Synology: fill any remaining empty download_station keys from shared [TORRENT]
    _torrent_client_map("download_station"),
)

# Kept empty on purpose: client maps must not go through migrate_legacy_maps.
# Clients use migrate_client_maps → [CLIENTS]; notifiers use [NOTIFIERS].
CLIENT_LEGACY_MAPS: tuple[LegacyMap, ...] = ()
METADATA_LEGACY_MAPS: tuple[LegacyMap, ...] = ()
PROVIDER_LEGACY_MAPS: tuple[LegacyMap, ...] = ()

ALL_LEGACY_MAPS: tuple[LegacyMap, ...] = NOTIFIER_LEGACY_MAPS + CLIENT_LEGACY_MAPS + METADATA_LEGACY_MAPS + PROVIDER_LEGACY_MAPS
