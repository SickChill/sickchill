from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin
from sickchill.plugins.settings import _as_bool


@register
class TraktNotifier(LegacyNotifierPlugin):
    id = "trakt"
    name = "Trakt"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_TRAKT"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Trakt",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_trakt",)),
        Field(name="username", type="str", default="", legacy_keys=("trakt_username",)),
        Field(name="api_key", type="str", default="", legacy_keys=("trakt_api_key",)),
        Field(name="api_secret", type="str", default="", legacy_keys=("trakt_api_secret",)),
        Field(name="access_token", type="str", default="", legacy_keys=("trakt_access_token",)),
        Field(name="refresh_token", type="str", default="", legacy_keys=("trakt_refresh_token",)),
        Field(name="remove_watchlist", type="bool", default=False, legacy_keys=("trakt_remove_watchlist",)),
        Field(name="remove_serieslist", type="bool", default=False, legacy_keys=("trakt_remove_serieslist",)),
        Field(name="remove_show_from_sickchill", type="bool", default=False, legacy_keys=("trakt_remove_show_from_sickchill",)),
        Field(name="sync_watchlist", type="bool", default=False, legacy_keys=("trakt_sync_watchlist",)),
        Field(name="method_add", type="int", default=0, legacy_keys=("trakt_method_add",)),
        Field(name="start_paused", type="bool", default=False, legacy_keys=("trakt_start_paused",)),
        Field(name="use_recommended", type="bool", default=False, legacy_keys=("trakt_use_recommended",)),
        Field(name="sync", type="bool", default=False, legacy_keys=("trakt_sync",)),
        Field(name="sync_remove", type="bool", default=False, legacy_keys=("trakt_sync_remove",)),
        Field(name="default_indexer", type="int", default=0, legacy_keys=("trakt_default_indexer",)),
        Field(name="timeout", type="int", default=0, legacy_keys=("trakt_timeout",)),
        Field(name="blacklist_name", type="str", default="", legacy_keys=("trakt_blacklist_name",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_TRAKT = bool(self.ctx.get("enabled"))
        settings.TRAKT_USERNAME = self.ctx.get("username") or ""
        settings.TRAKT_API_KEY = self.ctx.get("api_key") or ""
        settings.TRAKT_API_SECRET = self.ctx.get("api_secret") or ""
        settings.TRAKT_ACCESS_TOKEN = self.ctx.get("access_token") or ""
        settings.TRAKT_REFRESH_TOKEN = self.ctx.get("refresh_token") or ""
        settings.TRAKT_REMOVE_WATCHLIST = bool(self.ctx.get("remove_watchlist"))
        settings.TRAKT_REMOVE_SERIESLIST = bool(self.ctx.get("remove_serieslist"))
        settings.TRAKT_REMOVE_SHOW_FROM_SICKCHILL = bool(self.ctx.get("remove_show_from_sickchill"))
        settings.TRAKT_SYNC_WATCHLIST = bool(self.ctx.get("sync_watchlist"))
        try:
            settings.TRAKT_METHOD_ADD = int(self.ctx.get("method_add") or 0)
        except (TypeError, ValueError):
            settings.TRAKT_METHOD_ADD = 0
        settings.TRAKT_START_PAUSED = bool(self.ctx.get("start_paused"))
        settings.TRAKT_USE_RECOMMENDED = bool(self.ctx.get("use_recommended"))
        settings.TRAKT_SYNC = _as_bool(self.ctx.get("sync"), False)
        settings.TRAKT_SYNC_REMOVE = bool(self.ctx.get("sync_remove"))
        try:
            settings.TRAKT_DEFAULT_INDEXER = int(self.ctx.get("default_indexer") or 0)
        except (TypeError, ValueError):
            settings.TRAKT_DEFAULT_INDEXER = 0
        try:
            settings.TRAKT_TIMEOUT = int(self.ctx.get("timeout") or 0)
        except (TypeError, ValueError):
            settings.TRAKT_TIMEOUT = 0
        settings.TRAKT_BLACKLIST_NAME = self.ctx.get("blacklist_name") or ""
