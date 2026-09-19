from __future__ import annotations

import unittest

from sickchill.plugins.api import Field, Plugin, PluginContext, PluginKind, clear_registry, register
from sickchill.plugins.kinds.notifier import NotifierPlugin


class FieldValidationTests(unittest.TestCase):
    def tearDown(self):
        clear_registry()

    def test_required_and_types(self):
        @register
        class Fake(NotifierPlugin):
            id = "fake"
            name = "Fake"
            schema = (
                Field(name="count", type="int", required=True),
                Field(name="mode", type="select", choices=("a", "b"), default="a"),
                Field(name="flag", type="bool", default=False),
            )

        ctx = PluginContext(kind=PluginKind.NOTIFIER, plugin_id="fake", _data={})
        plugin = Fake(ctx)
        errors = plugin.validate()
        self.assertTrue(any("count is required" in e for e in errors))

        ctx.update(count="nope", mode="z", flag="maybe")
        errors = plugin.validate()
        self.assertTrue(any("integer" in e for e in errors))
        self.assertTrue(any("one of" in e for e in errors))
        self.assertTrue(any("boolean" in e for e in errors))

        ctx.update(count=3, mode="a", flag=True)
        self.assertEqual(plugin.validate(), [])


class RegisterTests(unittest.TestCase):
    def tearDown(self):
        clear_registry()

    def test_register_rejects_non_plugin(self):
        class NotAPlugin:
            pass

        with self.assertRaises(TypeError):
            register(NotAPlugin)  # type: ignore[arg-type]
