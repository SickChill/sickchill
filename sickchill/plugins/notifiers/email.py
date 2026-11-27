from __future__ import annotations

from typing import ClassVar

from sickchill import settings
from sickchill.plugins.api import Field, register
from sickchill.plugins.kinds.notifier import LegacyNotifierPlugin
from sickchill.plugins.settings import decrypt_stored_password


@register
class EmailNotifier(LegacyNotifierPlugin):
    id = "email"
    name = "Email"
    version = "1.0.0"
    impl_module: ClassVar[str] = "emailnotify"
    enable_setting: ClassVar[str] = "USE_EMAIL"
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
        settings.EMAIL_PASSWORD = decrypt_stored_password(self.ctx.get("password"))
        settings.EMAIL_FROM = self.ctx.get("from") or ""
        settings.EMAIL_LIST = self.ctx.get("list") or ""
        settings.EMAIL_SUBJECT = self.ctx.get("subject") or ""
