from __future__ import annotations

import logging
import unittest

from configobj import ConfigObj

from sickchill import settings
from sickchill.oldbeard.config import peek_setting_str
from sickchill.plugins.api import PluginKind, clear_registry
from sickchill.plugins.manager import PluginManager
from sickchill.plugins.metadata import FIRST_PARTY_METADATA_MODULES, load_first_party_metadata
from sickchill.plugins.metadata.config import (
    DEFAULT_PACKED,
    METADATA_FLAG_NAMES,
    METADATA_GENERATORS,
    migrate_metadata_from_general,
    pack_flags,
    packed_from_metadata_or_general,
    refresh_metadata_provider_dict,
    sync_metadata_from_settings,
    unpack_packed_config,
    write_metadata_to_cfg,
)
from sickchill.plugins.settings import ensure_metadata_section, read_metadata_section, write_metadata_section

EXPECTED_METADATA_IDS = frozenset({"kodi", "mediabrowser", "sony_ps3", "wdtv", "tivo", "mede8er"})


class MetadataPluginTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        self.manager = PluginManager()
        self._saved = {attr: getattr(settings, attr) for _, attr, *_ in METADATA_GENERATORS}
        self._saved_dict = getattr(settings, "metadata_provider_dict", {})

    def tearDown(self):
        clear_registry()
        for attr, value in self._saved.items():
            setattr(settings, attr, value)
        settings.metadata_provider_dict = self._saved_dict

    def test_load_first_party_metadata_registers_six_including_sony_ps3(self):
        load_first_party_metadata()
        self.manager.discover()
        classes = self.manager.classes(PluginKind.METADATA)
        ids = {cls.id for cls in classes}
        self.assertEqual(ids, EXPECTED_METADATA_IDS)
        self.assertEqual(set(FIRST_PARTY_METADATA_MODULES), EXPECTED_METADATA_IDS)
        self.assertIn("sony_ps3", ids)
        self.assertNotIn("ps3", ids)
        self.assertTrue(all(cls.kind == PluginKind.METADATA for cls in classes))

    def test_migrate_general_packed_to_metadata_strips_keys_keeps_general(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        packed = "0|1|0|1|0|1|0|0|0|0"
        cfg["General"] = {
            "metadata_kodi": packed,
            "metadata_mediabrowser": DEFAULT_PACKED,
            "other_setting": "keep-me",
        }

        with self.assertLogs("sickchill.plugins.metadata", level=logging.INFO) as logs:
            self.assertTrue(migrate_metadata_from_general(cfg))

        self.assertTrue(any("General.metadata_kodi -> METADATA[[kodi]]" in line for line in logs.output))
        kodi = read_metadata_section(cfg, "kodi")
        self.assertEqual(pack_flags(kodi), packed)
        self.assertTrue(kodi.get("episode_metadata") in (True, "True", "true", 1, "1"))
        self.assertTrue(kodi.get("poster") in (True, "True", "true", 1, "1"))
        self.assertTrue(kodi.get("episode_thumbnails") in (True, "True", "true", 1, "1"))

        self.assertIn("General", cfg)
        self.assertEqual(cfg["General"].get("other_setting"), "keep-me")
        self.assertNotIn("metadata_kodi", cfg["General"])
        self.assertNotIn("metadata_mediabrowser", cfg["General"])

    def test_peek_path_does_not_recreate_metadata_keys(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["METADATA"] = {
            "kodi": unpack_packed_config("1|0|0|0|0|0|0|0|0|0"),
        }
        cfg["General"] = {"root_dirs": "/tv"}

        before = set(cfg["General"].keys())
        self.assertEqual(peek_setting_str(cfg, "General", "metadata_kodi", DEFAULT_PACKED), DEFAULT_PACKED)
        self.assertEqual(packed_from_metadata_or_general(cfg, "kodi", "metadata_kodi"), "1|0|0|0|0|0|0|0|0|0")
        self.assertEqual(set(cfg["General"].keys()), before)
        self.assertNotIn("metadata_kodi", cfg["General"])
        self.assertNotIn("metadata_mediabrowser", cfg["General"])

    def test_sync_roundtrip_metadata_bools_and_packed(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        packed = "1|0|1|0|1|0|1|0|1|0"
        write_metadata_section(cfg, "kodi", unpack_packed_config(packed))

        settings.METADATA_KODI = DEFAULT_PACKED
        sync_metadata_from_settings(cfg)
        self.assertEqual(settings.METADATA_KODI, packed)

        settings.METADATA_KODI = "0|1|0|1|0|1|0|1|0|1"
        settings.METADATA_MEDIABROWSER = DEFAULT_PACKED
        settings.METADATA_PS3 = DEFAULT_PACKED
        settings.METADATA_WDTV = DEFAULT_PACKED
        settings.METADATA_TIVO = DEFAULT_PACKED
        settings.METADATA_MEDE8ER = DEFAULT_PACKED
        out = ConfigObj()
        out.indent_type = "  "
        write_metadata_to_cfg(out)
        self.assertEqual(pack_flags(read_metadata_section(out, "kodi")), "0|1|0|1|0|1|0|1|0|1")
        sync_metadata_from_settings(out)
        self.assertEqual(settings.METADATA_KODI, "0|1|0|1|0|1|0|1|0|1")

    def test_write_metadata_to_cfg_strips_general_metadata_keys(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["General"] = {
            "metadata_kodi": "1|0|0|0|0|0|0|0|0|0",
            "metadata_ps3": "0|0|0|0|0|0|0|0|0|0",
            "keep": "yes",
        }
        settings.METADATA_KODI = "0|0|1|0|0|0|0|0|0|0"
        settings.METADATA_MEDIABROWSER = DEFAULT_PACKED
        settings.METADATA_PS3 = DEFAULT_PACKED
        settings.METADATA_WDTV = DEFAULT_PACKED
        settings.METADATA_TIVO = DEFAULT_PACKED
        settings.METADATA_MEDE8ER = DEFAULT_PACKED

        write_metadata_to_cfg(cfg)
        self.assertNotIn("metadata_kodi", cfg["General"])
        self.assertNotIn("metadata_ps3", cfg["General"])
        self.assertEqual(cfg["General"].get("keep"), "yes")
        self.assertEqual(pack_flags(read_metadata_section(cfg, "kodi")), "0|0|1|0|0|0|0|0|0|0")
        self.assertIn("METADATA", cfg)
        self.assertNotIn("extensions", cfg)

    def test_manager_get_metadata_without_enabled(self):
        load_first_party_metadata()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_metadata_section(cfg, "kodi", unpack_packed_config("1|1|0|0|0|0|0|0|0|0"))
        self.manager._cfg = cfg
        self.manager.discover()

        plugin = self.manager.instance(PluginKind.METADATA, "kodi")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.as_packed_config(), "1|1|0|0|0|0|0|0|0|0")
        self.assertNotEqual(plugin.ctx.get("enabled"), True)

        via_get = self.manager.get(PluginKind.METADATA, "kodi")
        self.assertIs(plugin, via_get)

    def test_idempotent_migrate_silent_mutated_false(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["General"] = {"metadata_kodi": "1|0|0|1|0|0|0|0|0|0", "keep": "1"}
        self.assertTrue(migrate_metadata_from_general(cfg))
        self.assertNotIn("metadata_kodi", cfg["General"])

        with self.assertNoLogs("sickchill.plugins.metadata", level=logging.INFO):
            self.assertFalse(migrate_metadata_from_general(cfg))

        self.assertEqual(pack_flags(read_metadata_section(cfg, "kodi")), "1|0|0|1|0|0|0|0|0|0")
        self.assertIn("General", cfg)

    def test_refresh_metadata_provider_dict_wires_names(self):
        settings.METADATA_KODI = "1|0|0|0|0|0|0|0|0|0"
        settings.METADATA_MEDIABROWSER = DEFAULT_PACKED
        settings.METADATA_PS3 = DEFAULT_PACKED
        settings.METADATA_WDTV = DEFAULT_PACKED
        settings.METADATA_TIVO = DEFAULT_PACKED
        settings.METADATA_MEDE8ER = DEFAULT_PACKED
        refresh_metadata_provider_dict()
        self.assertIn("KODI", settings.metadata_provider_dict)
        self.assertIn("Sony PS3", settings.metadata_provider_dict)
        self.assertTrue(settings.metadata_provider_dict["KODI"].show_metadata)
        self.assertEqual(len(settings.metadata_provider_dict), 6)

    def test_pack_unpack_flag_order(self):
        flags = {name: False for name in METADATA_FLAG_NAMES}
        flags["episode_metadata"] = True
        flags["poster"] = True
        packed = pack_flags(flags)
        self.assertEqual(packed, "0|1|0|1|0|0|0|0|0|0")
        self.assertEqual(unpack_packed_config(packed)["episode_metadata"], True)
        self.assertEqual(unpack_packed_config(packed)["poster"], True)

    def test_ensure_metadata_section_top_level(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        section = ensure_metadata_section(cfg, "kodi")
        self.assertIs(section, cfg["METADATA"]["kodi"])
        self.assertNotIn("extensions", cfg)
