from __future__ import annotations

import textwrap
import unittest
from pathlib import Path

from sickchill.plugins.api import Plugin, clear_registry
from sickchill.plugins.loader import discover_classes, discover_dropins


class LoaderTests(unittest.TestCase):
    def tearDown(self):
        clear_registry()

    def test_dropin_discovered(self):
        with self._tmp_plugins() as root:
            plugin_dir = root / "sample"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.py").write_text(
                textwrap.dedent(
                    """
                    from sickchill.plugins.api import Plugin, PluginKind
                    from sickchill.plugins.kinds.notifier import NotifierPlugin

                    class DropIn(NotifierPlugin):
                        id = "dropin"
                        name = "Drop In"
                    """
                ),
                encoding="utf-8",
            )
            classes = discover_dropins(root)
            self.assertEqual(len(classes), 1)
            self.assertEqual(classes[0].id, "dropin")
            self.assertTrue(issubclass(classes[0], Plugin))

    def test_bad_dropin_does_not_raise(self):
        with self._tmp_plugins() as root:
            bad = root / "broken"
            bad.mkdir()
            (bad / "plugin.py").write_text("this is not valid python {{{", encoding="utf-8")
            classes = discover_classes(plugins_dir=str(root))
            self.assertIsInstance(classes, list)

    def test_non_plugin_rejected(self):
        with self._tmp_plugins() as root:
            plugin_dir = root / "nope"
            plugin_dir.mkdir()
            (plugin_dir / "plugin.py").write_text(
                textwrap.dedent(
                    """
                    class NotPlugin:
                        id = "nope"
                        name = "Nope"
                    """
                ),
                encoding="utf-8",
            )
            classes = discover_dropins(root)
            self.assertEqual(classes, [])

    def _tmp_plugins(self):
        import tempfile
        from contextlib import contextmanager

        @contextmanager
        def ctx():
            with tempfile.TemporaryDirectory() as tmp:
                yield Path(tmp)

        return ctx()
