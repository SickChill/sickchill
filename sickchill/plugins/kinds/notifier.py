from __future__ import annotations

from typing import ClassVar

from sickchill.plugins.api import Plugin, PluginKind


class NotifierPlugin(Plugin):
    kind: ClassVar[PluginKind] = PluginKind.NOTIFIER

    def notify_snatch(self, *args, **kwargs) -> None:
        return None

    def notify_download(self, *args, **kwargs) -> None:
        return None

    def notify_postprocess(self, *args, **kwargs) -> None:
        return None

    def notify_subtitle_download(self, *args, **kwargs) -> None:
        return None

    def notify_update(self, *args, **kwargs) -> None:
        return None

    def notify_login(self, *args, **kwargs) -> None:
        return None

    def notify_logged_error(self, *args, **kwargs) -> None:
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


class LegacyNotifierPlugin(NotifierPlugin):
    """Schema/settings wrapper around ``sickchill.notifiers.<impl_module>.Notifier``."""

    version = "1.0.0"
    impl_module: ClassVar[str] = ""
    enable_setting: ClassVar[str] = ""

    def _sync_settings(self) -> None:
        return None

    def _impl(self):
        import importlib

        module_name = self.impl_module or self.id
        mod = importlib.import_module(f"sickchill.notifiers.{module_name}")
        return mod.Notifier()

    def _forward(self, method: str, *args, **kwargs):
        self._sync_settings()
        impl = self._impl()
        fn = getattr(impl, method, None)
        if callable(fn):
            return fn(*args, **kwargs)
        return None

    def notify_snatch(self, ep_name, *args, **kwargs):
        return self._forward("notify_snatch", ep_name, *args, **kwargs)

    def notify_download(self, ep_name, *args, **kwargs):
        return self._forward("notify_download", ep_name, *args, **kwargs)

    def notify_postprocess(self, ep_name, *args, **kwargs):
        return self._forward("notify_postprocess", ep_name, *args, **kwargs)

    def notify_subtitle_download(self, ep_name, lang="", *args, **kwargs):
        return self._forward("notify_subtitle_download", ep_name, lang, *args, **kwargs)

    def notify_update(self, new_version="??", *args, **kwargs):
        return self._forward("notify_update", new_version, *args, **kwargs)

    def notify_login(self, ipaddress="", *args, **kwargs):
        return self._forward("notify_login", ipaddress, *args, **kwargs)

    def notify_logged_error(self, ui_error, *args, **kwargs):
        return self._forward("notify_logged_error", ui_error, *args, **kwargs)

    def update_library(self, *args, **kwargs):
        return self._forward("update_library", *args, **kwargs)

    def test_notify(self, *args, **kwargs):
        from sickchill import settings

        self._sync_settings()
        previous = None
        restored = False
        if self.enable_setting and hasattr(settings, self.enable_setting):
            previous = getattr(settings, self.enable_setting)
            setattr(settings, self.enable_setting, True)
            restored = True
        try:
            impl = self._impl()
            if hasattr(impl, "test_notify"):
                return impl.test_notify(*args, **kwargs)
            if hasattr(impl, "test_notify_pms"):
                return impl.test_notify_pms(*args, **kwargs)
            return False
        finally:
            if restored:
                setattr(settings, self.enable_setting, previous)

    def test(self) -> tuple[bool, str]:
        try:
            result = self.test_notify()
        except Exception as error:
            return False, str(error)
        if isinstance(result, tuple):
            return bool(result[0]), str(result[1] if len(result) > 1 else result[0])
        if result is None:
            return True, "ok"
        if result is False:
            return False, "failed"
        if isinstance(result, str) and result:
            return False, result
        return bool(result), "ok" if result else "failed"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        self._sync_settings()
        return getattr(self._impl(), name)
