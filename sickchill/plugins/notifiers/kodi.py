from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin
from sickchill.plugins.settings import decrypt_stored_password


@register
class KodiNotifier(LegacyNotifierPlugin):
    id = "kodi"
    name = "Kodi"
    version = "1.0.0"
    enable_setting: ClassVar[str] = "USE_KODI"
    legacy_sections: ClassVar[tuple[str, ...]] = ("KODI",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_kodi",)),
        Field(name="always_on", type="bool", default=False, legacy_keys=("kodi_always_on",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("kodi_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("kodi_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("kodi_notify_onsubtitledownload",)),
        Field(name="update_library", type="bool", default=False, legacy_keys=("kodi_update_library",)),
        Field(name="update_full", type="bool", default=False, legacy_keys=("kodi_update_full",)),
        Field(name="update_onlyfirst", type="bool", default=False, legacy_keys=("kodi_update_onlyfirst",)),
        Field(name="host", type="str", default="", legacy_keys=("kodi_host",)),
        Field(name="username", type="str", default="", legacy_keys=("kodi_username",)),
        Field(name="password", type="str", default="", legacy_keys=("kodi_password",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_KODI = bool(self.ctx.get("enabled"))
        settings.KODI_ALWAYS_ON = bool(self.ctx.get("always_on"))
        settings.KODI_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.KODI_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.KODI_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.KODI_UPDATE_LIBRARY = bool(self.ctx.get("update_library"))
        settings.KODI_UPDATE_FULL = bool(self.ctx.get("update_full"))
        settings.KODI_UPDATE_ONLYFIRST = bool(self.ctx.get("update_onlyfirst"))
        settings.KODI_HOST = self.ctx.get("host") or ""
        settings.KODI_USERNAME = self.ctx.get("username") or ""
        settings.KODI_PASSWORD = decrypt_stored_password(self.ctx.get("password"))

    def test_notify(self, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "test_notify"):
            if not args and "host" not in kwargs:
                kwargs = dict(kwargs, host=settings.KODI_HOST, username=settings.KODI_USERNAME, password=settings.KODI_PASSWORD)
            return impl.test_notify(*args, **kwargs)
        if hasattr(impl, "test_notify_pms"):
            return impl.test_notify_pms(*args, **kwargs)
        return False
