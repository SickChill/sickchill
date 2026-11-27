from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin


@register
class TwitterNotifier(LegacyNotifierPlugin):
    id = "twitter"
    name = "Twitter"
    version = "1.0.0"
    impl_module: ClassVar[str] = "tweet"
    enable_setting: ClassVar[str] = "USE_TWITTER"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Twitter",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_twitter",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("twitter_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("twitter_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("twitter_notify_onsubtitledownload",)),
        Field(name="username", type="str", default="", legacy_keys=("twitter_username",)),
        Field(name="password", type="str", default="", legacy_keys=("twitter_password",)),
        Field(name="prefix", type="str", default="", legacy_keys=("twitter_prefix",)),
        Field(name="dmto", type="str", default="", legacy_keys=("twitter_dmto",)),
        Field(name="usedm", type="bool", default=False, legacy_keys=("twitter_usedm",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_TWITTER = bool(self.ctx.get("enabled"))
        settings.TWITTER_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.TWITTER_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.TWITTER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.TWITTER_USERNAME = self.ctx.get("username") or ""
        settings.TWITTER_PASSWORD = self.ctx.get("password") or ""
        settings.TWITTER_PREFIX = self.ctx.get("prefix") or ""
        settings.TWITTER_DMTO = self.ctx.get("dmto") or ""
        settings.TWITTER_USEDM = bool(self.ctx.get("usedm"))
