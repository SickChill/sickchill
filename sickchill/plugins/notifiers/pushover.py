from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class PushoverNotifier(NotifierPlugin):
    id = "pushover"
    name = "Pushover"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Pushover",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_pushover",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("pushover_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("pushover_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("pushover_notify_onsubtitledownload",)),
        Field(name="userkey", type="str", default="", legacy_keys=("pushover_userkey",)),
        Field(name="apikey", type="str", default="", legacy_keys=("pushover_apikey",)),
        Field(name="device", type="str", default="", legacy_keys=("pushover_device",)),
        Field(name="sound", type="str", default="", legacy_keys=("pushover_sound",)),
        Field(name="priority", type="str", default="", legacy_keys=("pushover_priority",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_PUSHOVER = bool(self.ctx.get("enabled"))
        settings.PUSHOVER_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.PUSHOVER_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.PUSHOVER_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.PUSHOVER_USERKEY = self.ctx.get("userkey") or ""
        settings.PUSHOVER_APIKEY = self.ctx.get("apikey") or ""
        settings.PUSHOVER_DEVICE = self.ctx.get("device") or ""
        settings.PUSHOVER_SOUND = self.ctx.get("sound") or ""
        settings.PUSHOVER_PRIORITY = self.ctx.get("priority") or ""

    def _impl(self):
        from sickchill.oldbeard.notifiers import pushover as _mod

        return _mod.Notifier()

    def notify_snatch(self, ep_name, *args, **kwargs):
        self._sync_settings()
        return self._impl().notify_snatch(ep_name, *args, **kwargs)

    def notify_download(self, ep_name, *args, **kwargs):
        self._sync_settings()
        return self._impl().notify_download(ep_name, *args, **kwargs)

    def notify_postprocess(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_postprocess"):
            return impl.notify_postprocess(ep_name, *args, **kwargs)
        return None

    def notify_subtitle_download(self, ep_name, lang="", *args, **kwargs):
        self._sync_settings()
        return self._impl().notify_subtitle_download(ep_name, lang, *args, **kwargs)

    def notify_update(self, new_version="??", *args, **kwargs):
        self._sync_settings()
        return self._impl().notify_update(new_version, *args, **kwargs)

    def notify_login(self, ipaddress="", *args, **kwargs):
        self._sync_settings()
        return self._impl().notify_login(ipaddress, *args, **kwargs)

    def notify_logged_error(self, ui_error, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_logged_error"):
            return impl.notify_logged_error(ui_error, *args, **kwargs)
        return None

    def test_notify(self, *args, **kwargs):
        self._sync_settings()
        settings.USE_PUSHOVER = True
        return self._impl().test_notify(*args, **kwargs)

    def test(self):
        result = self.test_notify()
        if isinstance(result, tuple):
            return bool(result[0]), str(result[1] if len(result) > 1 else result[0])
        return bool(result), "ok" if result else "failed"
