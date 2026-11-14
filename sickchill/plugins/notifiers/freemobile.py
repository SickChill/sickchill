from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class FreemobileNotifier(NotifierPlugin):
    id = "freemobile"
    name = "Freemobile"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("FreeMobile",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_freemobile",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("freemobile_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("freemobile_notify_ondownload",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("freemobile_notify_onsubtitledownload",)),
        Field(name="id", type="str", default="", legacy_keys=("freemobile_id",)),
        Field(name="apikey", type="str", default="", legacy_keys=("freemobile_apikey",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_FREEMOBILE = bool(self.ctx.get("enabled"))
        settings.FREEMOBILE_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.FREEMOBILE_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.FREEMOBILE_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.FREEMOBILE_ID = self.ctx.get("id") or ""
        settings.FREEMOBILE_APIKEY = self.ctx.get("apikey") or ""

    def _impl(self):
        from sickchill.oldbeard.notifiers import freemobile as _mod

        return _mod.Notifier()

    def notify_snatch(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_snatch"):
            return impl.notify_snatch(ep_name, *args, **kwargs)
        return None

    def notify_download(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_download"):
            return impl.notify_download(ep_name, *args, **kwargs)
        return None

    def notify_postprocess(self, ep_name, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_postprocess"):
            return impl.notify_postprocess(ep_name, *args, **kwargs)
        return None

    def notify_subtitle_download(self, ep_name, lang="", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_subtitle_download"):
            return impl.notify_subtitle_download(ep_name, lang, *args, **kwargs)
        return None

    def notify_update(self, new_version="??", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_update"):
            return impl.notify_update(new_version, *args, **kwargs)
        return None

    def notify_login(self, ipaddress="", *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_login"):
            return impl.notify_login(ipaddress, *args, **kwargs)
        return None

    def notify_logged_error(self, ui_error, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "notify_logged_error"):
            return impl.notify_logged_error(ui_error, *args, **kwargs)
        return None

    def test_notify(self, *args, **kwargs):
        self._sync_settings()
        previous = settings.USE_FREEMOBILE
        settings.USE_FREEMOBILE = True
        try:
            impl = self._impl()
            if hasattr(impl, "test_notify"):
                return impl.test_notify(*args, **kwargs)
            if hasattr(impl, "test_notify_pms"):
                return impl.test_notify_pms(*args, **kwargs)
            return False
        finally:
            settings.USE_FREEMOBILE = previous

    def test(self):
        result = self.test_notify()
        if isinstance(result, tuple):
            return bool(result[0]), str(result[1] if len(result) > 1 else result[0])
        return bool(result), "ok" if result else "failed"

    def update_library(self, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        if hasattr(impl, "update_library"):
            return impl.update_library(*args, **kwargs)
        return None

    def __getattr__(self, name):
        # Forward library helpers (addFolder, update_watchlist, play_episode, ...)
        if name.startswith("_"):
            raise AttributeError(name)
        self._sync_settings()
        impl = self._impl()
        return getattr(impl, name)
