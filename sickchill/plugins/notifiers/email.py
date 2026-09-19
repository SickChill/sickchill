from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


@register
class EmailNotifier(NotifierPlugin):
    id = "email"
    name = "Email"
    version = "1.0.0"
    legacy_sections: ClassVar[tuple[str, ...]] = ("Email",)
    schema: ClassVar[tuple[Field, ...]] = (
        Field(name="enabled", type="bool", default=False, legacy_keys=("use_email",)),
        Field(name="notify_onsnatch", type="bool", default=False, legacy_keys=("email_notify_onsnatch",)),
        Field(name="notify_ondownload", type="bool", default=False, legacy_keys=("email_notify_ondownload",)),
        Field(name="notify_onpostprocess", type="bool", default=False, legacy_keys=("email_notify_onpostprocess",)),
        Field(name="notify_onsubtitledownload", type="bool", default=False, legacy_keys=("email_notify_onsubtitledownload",)),
        Field(name="host", type="str", default="", legacy_keys=("email_host",)),
        Field(name="port", type="int", default=0, legacy_keys=("email_port",)),
        Field(name="tls", type="bool", default=False, legacy_keys=("email_tls",)),
        Field(name="user", type="str", default="", legacy_keys=("email_user",)),
        Field(name="password", type="str", default="", legacy_keys=("email_password",)),
        Field(name="from", type="str", default="", legacy_keys=("email_from",)),
        Field(name="list", type="str", default="", legacy_keys=("email_list",)),
        Field(name="subject", type="str", default="", legacy_keys=("email_subject",)),
    )

    def _sync_settings(self) -> None:
        settings.USE_EMAIL = bool(self.ctx.get("enabled"))
        settings.EMAIL_NOTIFY_ONSNATCH = bool(self.ctx.get("notify_onsnatch"))
        settings.EMAIL_NOTIFY_ONDOWNLOAD = bool(self.ctx.get("notify_ondownload"))
        settings.EMAIL_NOTIFY_ONPOSTPROCESS = bool(self.ctx.get("notify_onpostprocess"))
        settings.EMAIL_NOTIFY_ONSUBTITLEDOWNLOAD = bool(self.ctx.get("notify_onsubtitledownload"))
        settings.EMAIL_HOST = self.ctx.get("host") or ""
        try:
            settings.EMAIL_PORT = int(self.ctx.get("port") or 0)
        except (TypeError, ValueError):
            settings.EMAIL_PORT = 0
        settings.EMAIL_TLS = bool(self.ctx.get("tls"))
        settings.EMAIL_USER = self.ctx.get("user") or ""
        settings.EMAIL_PASSWORD = self.ctx.get("password") or ""
        settings.EMAIL_FROM = self.ctx.get("from") or ""
        settings.EMAIL_LIST = self.ctx.get("list") or ""
        settings.EMAIL_SUBJECT = self.ctx.get("subject") or ""

    def _impl(self):
        from sickchill.oldbeard.notifiers import emailnotify as _mod

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
        previous = settings.USE_EMAIL
        settings.USE_EMAIL = True
        try:
            impl = self._impl()
            if hasattr(impl, "test_notify"):
                return impl.test_notify(*args, **kwargs)
            if hasattr(impl, "test_notify_pms"):
                return impl.test_notify_pms(*args, **kwargs)
            return False
        finally:
            settings.USE_EMAIL = previous

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
