from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import Plugin, PluginKind


class NotifierPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.NOTIFIER

    def notify_snatch(self, title: str, message: str = "") -> None:
        return None

    def notify_download(self, title: str, message: str = "") -> None:
        return None

    def notify_postprocess(self, title: str, message: str = "") -> None:
        return None

    def notify_subtitle_download(self, title: str, message: str = "") -> None:
        return None

    def notify_update(self, title: str, message: str = "") -> None:
        return None

    def notify_login(self, title: str, message: str = "") -> None:
        return None

    def notify_logged_error(self, title: str, message: str = "") -> None:
        return None

    def test(self) -> tuple[bool, str]:
        test_notify = getattr(self, "test_notify", None)
        if callable(test_notify):
            try:
                result = test_notify()
            except Exception as error:
                return False, str(error)
            if isinstance(result, tuple) and len(result) == 2:
                return bool(result[0]), str(result[1])
            return bool(result), "ok" if result else "failed"
        return super().test()
