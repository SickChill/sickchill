from __future__ import annotations

import unittest

from configobj import ConfigObj

from sickchill.plugins.api import PluginKind, clear_registry
from sickchill.plugins.clients import FIRST_PARTY_CLIENT_MODULES, load_first_party_clients
from sickchill.plugins.clients.config import sync_clients_from_settings, write_clients_to_cfg
from sickchill.plugins.legacy_maps import CLIENT_LEGACY_MAPS, CLIENT_SECTION_MAPS, TORRENT_CLIENT_IDS
from sickchill.plugins.manager import PluginManager
from sickchill.plugins.settings import (
    ensure_client_section,
    migrate_client_maps,
    migrate_legacy_maps,
    read_client_section,
    write_client_section,
)

EXPECTED_CLIENT_IDS = frozenset(
    {
        "blackhole",
        "deluge",
        "deluged",
        "download_station",
        "mlnet",
        "nzbget",
        "putio",
        "qbittorrent",
        "rtorrent",
        "sabnzbd",
        "transmission",
        "utorrent",
    }
)


class ClientPluginTests(unittest.TestCase):
    def setUp(self):
        clear_registry()
        self.manager = PluginManager()

    def tearDown(self):
        clear_registry()

    def test_load_first_party_clients_registers_all_twelve(self):
        load_first_party_clients()
        self.manager.discover()
        classes = self.manager.classes(PluginKind.CLIENT)
        ids = {cls.id for cls in classes}
        self.assertEqual(ids, EXPECTED_CLIENT_IDS)
        self.assertEqual(set(FIRST_PARTY_CLIENT_MODULES), EXPECTED_CLIENT_IDS)
        self.assertIn("blackhole", ids)
        # No provider ids accidentally registered as clients
        self.assertTrue(all(cls.kind == PluginKind.CLIENT for cls in classes))

    def test_migrate_torrent_seeds_clients_and_deletes_section(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["TORRENT"] = {
            "torrent_host": "http://localhost:9091",
            "torrent_username": "user",
            "torrent_password": "pass",
            "torrent_path": "/downloads",
            "torrent_path_incomplete": "/incomplete",
            "torrent_label": "tv",
            "torrent_label_anime": "anime",
            "torrent_paused": True,
            "torrent_seed_time": "42",
            "torrent_verify_cert": True,
            "torrent_rpcurl": "transmission",
            "torrent_high_bandwidth": True,
            "torrent_auth_type": "basic",
        }

        self.assertTrue(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        self.assertNotIn("TORRENT", cfg)

        transmission = read_client_section(cfg, "transmission")
        self.assertEqual(transmission.get("host"), "http://localhost:9091")
        self.assertEqual(transmission.get("username"), "user")
        self.assertEqual(transmission.get("rpcurl"), "transmission")
        self.assertTrue(transmission.get("high_bandwidth") in (True, "True", "true", 1, "1"))

        rtorrent = read_client_section(cfg, "rtorrent")
        self.assertEqual(rtorrent.get("host"), "http://localhost:9091")
        self.assertEqual(rtorrent.get("auth_type"), "basic")

        for client_id in TORRENT_CLIENT_IDS:
            section = read_client_section(cfg, client_id)
            self.assertEqual(section.get("host"), "http://localhost:9091", client_id)
            self.assertEqual(section.get("username"), "user", client_id)

        # No Synology section: download_station still gets shared TORRENT seed
        ds = read_client_section(cfg, "download_station")
        self.assertEqual(ds.get("host"), "http://localhost:9091")
        self.assertEqual(ds.get("username"), "user")

        # Idempotent: second migrate does not error or clear values
        self.assertFalse(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        self.assertEqual(read_client_section(cfg, "transmission").get("host"), "http://localhost:9091")

    def test_migrate_sab_nzbget_blackhole(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["SABnzbd"] = {"sab_host": "http://sab:8080", "sab_apikey": "key", "sab_username": "sab"}
        cfg["NZBget"] = {"nzbget_host": "nzbget:6789", "nzbget_username": "nzb", "nzbget_priority": "50"}
        cfg["Blackhole"] = {"nzb_dir": "/nzb", "torrent_dir": "/torrent"}

        self.assertTrue(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        self.assertNotIn("SABnzbd", cfg)
        self.assertNotIn("NZBget", cfg)
        self.assertNotIn("Blackhole", cfg)

        self.assertEqual(read_client_section(cfg, "sabnzbd").get("host"), "http://sab:8080")
        self.assertEqual(read_client_section(cfg, "sabnzbd").get("apikey"), "key")
        self.assertEqual(read_client_section(cfg, "nzbget").get("host"), "nzbget:6789")
        self.assertEqual(read_client_section(cfg, "nzbget").get("username"), "nzb")
        self.assertEqual(read_client_section(cfg, "blackhole").get("nzb_dir"), "/nzb")
        self.assertEqual(read_client_section(cfg, "blackhole").get("torrent_dir"), "/torrent")

    def test_synology_dsm_moves_to_download_station_keeps_use_synoindex(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["Synology"] = {
            "host": "http://dsm:5000",
            "username": "admin",
            "password": "secret",
            "path": "/volume1/downloads",
            "use_synoindex": True,
        }

        self.assertTrue(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        ds = read_client_section(cfg, "download_station")
        self.assertEqual(ds.get("host"), "http://dsm:5000")
        self.assertEqual(ds.get("username"), "admin")
        self.assertEqual(ds.get("password"), "secret")
        self.assertEqual(ds.get("path"), "/volume1/downloads")

        self.assertIn("Synology", cfg)
        self.assertEqual(cfg["Synology"].get("use_synoindex"), True)
        self.assertNotIn("host", cfg["Synology"])
        self.assertNotIn("username", cfg["Synology"])
        self.assertNotIn("password", cfg["Synology"])
        self.assertNotIn("path", cfg["Synology"])

    def test_download_station_prefers_synology_over_torrent(self):
        """When both [TORRENT] and [Synology] exist, DSM credentials win for download_station."""
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["TORRENT"] = {
            "torrent_host": "http://torrent-shared:9091",
            "torrent_username": "torrent-user",
            "torrent_password": "torrent-pass",
            "torrent_path": "/torrent-path",
        }
        cfg["Synology"] = {
            "host": "http://dsm:5000",
            "username": "admin",
            "password": "secret",
            "path": "/volume1/downloads",
            "use_synoindex": True,
        }

        self.assertTrue(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        ds = read_client_section(cfg, "download_station")
        self.assertEqual(ds.get("host"), "http://dsm:5000")
        self.assertEqual(ds.get("username"), "admin")
        self.assertEqual(ds.get("password"), "secret")
        self.assertEqual(ds.get("path"), "/volume1/downloads")
        # Other torrent clients still get the shared TORRENT seed
        self.assertEqual(read_client_section(cfg, "transmission").get("host"), "http://torrent-shared:9091")
        self.assertEqual(cfg["Synology"].get("use_synoindex"), True)

    def test_manager_instance_client_without_enabled(self):
        load_first_party_clients()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_client_section(cfg, "transmission", {"host": "http://localhost:9091", "username": "u"})
        self.manager._cfg = cfg
        self.manager.discover()

        plugin = self.manager.instance(PluginKind.CLIENT, "transmission")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.ctx.get("host"), "http://localhost:9091")
        # No enabled=True required
        self.assertNotEqual(plugin.ctx.get("enabled"), True)

        via_get = self.manager.get(PluginKind.CLIENT, "transmission")
        self.assertIs(plugin, via_get)

    def test_read_write_clients_section(self):
        cfg = ConfigObj()
        cfg.indent_type = "  "
        section = ensure_client_section(cfg, "transmission")
        self.assertIs(section, cfg["CLIENTS"]["transmission"])
        write_client_section(cfg, "transmission", {"host": "http://t:9091", "username": "bob"})
        self.assertEqual(read_client_section(cfg, "transmission"), {"host": "http://t:9091", "username": "bob"})
        self.assertNotIn("extensions", cfg)

    def test_client_maps_do_not_use_extensions_path(self):
        self.assertEqual(CLIENT_LEGACY_MAPS, ())
        cfg = ConfigObj()
        cfg.indent_type = "  "
        cfg["TORRENT"] = {"torrent_host": "http://localhost:9091"}
        # extensions migrator must not consume TORRENT / create extensions.clients
        self.assertFalse(migrate_legacy_maps(cfg, CLIENT_LEGACY_MAPS))
        self.assertIn("TORRENT", cfg)
        self.assertNotIn("extensions", cfg)

        self.assertTrue(migrate_client_maps(cfg, CLIENT_SECTION_MAPS))
        self.assertIn("CLIENTS", cfg)
        self.assertNotIn("extensions", cfg)
        self.assertNotIn("TORRENT", cfg)

    def test_send_keeps_username_when_adapter_passes_none(self):
        """Snatch calls Client() with no creds; must not blank TORRENT_USERNAME from empty ctx."""
        from sickchill import settings as sc_settings
        from sickchill.oldbeard.clients import getClientInstance
        from sickchill.plugins.manager import plugin_manager

        load_first_party_clients()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_client_section(
            cfg,
            "qbittorrent",
            {"host": "http://localhost:8080", "username": "sickchill", "password": "secret"},
        )
        plugin_manager._cfg = cfg
        plugin_manager.discover()
        plugin_manager._instances.clear()

        # Simulate a stale cached plugin whose ctx lost username after a bad sync
        stale = plugin_manager.get(PluginKind.CLIENT, "qbittorrent")
        self.assertIsNotNone(stale)
        stale.ctx._data["username"] = ""
        sc_settings.TORRENT_USERNAME = "sickchill"
        sc_settings.TORRENT_PASSWORD = "secret"
        sc_settings.TORRENT_HOST = "http://localhost:8080"

        host, username, password = stale._resolve_credentials(None, None, None)
        self.assertEqual(username, "sickchill")
        self.assertEqual(password, "secret")
        self.assertEqual(host, "http://localhost:8080")
        self.assertEqual(sc_settings.TORRENT_USERNAME, "sickchill")

        adapter = getClientInstance("qbittorrent")()
        host, username, password = adapter._plugin()._resolve_credentials(adapter.host, adapter.username, adapter.password)
        self.assertEqual(username, "sickchill")

    def test_torrent_impl_accepts_qbittorrent_positional_ctor(self):
        """qBittorrent.Client first arg is named `url`; wrappers must not pass host=."""
        from sickchill.oldbeard.clients import getClientInstance
        from sickchill.plugins.manager import plugin_manager

        load_first_party_clients()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_client_section(cfg, "qbittorrent", {"host": "http://localhost:8080"})
        plugin_manager._cfg = cfg
        plugin_manager.discover()
        plugin = plugin_manager.get(PluginKind.CLIENT, "qbittorrent")
        self.assertIsNotNone(plugin)
        client = plugin._impl("http://localhost:8080", "user", "pass")
        self.assertEqual(client.host, "http://localhost:8080")
        self.assertEqual(client.username, "user")
        self.assertEqual(client.password, "pass")

        adapter = getClientInstance("qbittorrent")("http://localhost:8080", "user", "pass")
        # Adapter path used by home.testTorrent — must not TypeError on host=
        self.assertTrue(hasattr(adapter, "test_client_connection"))
        built = adapter._plugin()._impl(adapter.host, adapter.username, adapter.password)
        self.assertEqual(built.username, "user")

    def test_all_torrent_clients_snatch_path_keeps_credentials(self):
        """Every torrent ClientPlugin: snatch-style Client() with no args keeps host/user/pass."""
        from sickchill import settings as sc_settings
        from sickchill.oldbeard.clients import getClientInstance
        from sickchill.plugins.manager import plugin_manager

        torrent_ids = (
            "transmission",
            "utorrent",
            "deluge",
            "deluged",
            "qbittorrent",
            "rtorrent",
            "mlnet",
            "putio",
            "download_station",
        )
        load_first_party_clients()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        for client_id in torrent_ids:
            write_client_section(
                cfg,
                client_id,
                {
                    "host": f"http://localhost/{client_id}",
                    "username": f"user-{client_id}",
                    "password": f"pass-{client_id}",
                    "path": f"/path/{client_id}",
                    "rpcurl": "transmission",
                    "auth_type": "none",
                },
            )

        plugin_manager._cfg = cfg
        plugin_manager.discover()
        plugin_manager._instances.clear()
        sc_settings.TORRENT_RPCURL = "transmission"

        for client_id in torrent_ids:
            with self.subTest(client_id=client_id):
                plugin_manager._instances.clear()
                sc_settings.TORRENT_HOST = ""
                sc_settings.TORRENT_USERNAME = ""
                sc_settings.TORRENT_PASSWORD = ""
                sc_settings.SYNOLOGY_DSM_HOST = ""
                sc_settings.SYNOLOGY_DSM_USERNAME = ""
                sc_settings.SYNOLOGY_DSM_PASSWORD = ""

                plugin = plugin_manager.get(PluginKind.CLIENT, client_id)
                self.assertIsNotNone(plugin, client_id)
                # Stale empty ctx must not win over [CLIENTS] reload
                plugin.ctx._data["username"] = ""
                plugin.ctx._data["password"] = ""
                plugin.ctx._data["host"] = ""

                host, username, password = plugin._resolve_credentials(None, None, None)
                self.assertEqual(host, f"http://localhost/{client_id}", client_id)
                self.assertEqual(username, f"user-{client_id}", client_id)
                self.assertEqual(password, f"pass-{client_id}", client_id)

                client = plugin._impl(host, username, password)
                self.assertEqual(client.username, f"user-{client_id}", client_id)
                self.assertEqual(client.password, f"pass-{client_id}", client_id)
                self.assertTrue(client.host, client_id)

                # Facade used by search.snatch_episode
                adapter = getClientInstance(client_id)()
                resolved = adapter._plugin()._resolve_credentials(adapter.host, adapter.username, adapter.password)
                self.assertEqual(resolved[1], f"user-{client_id}", client_id)

    def test_sab_nzbget_sync_does_not_blank_credentials(self):
        from sickchill import settings as sc_settings
        from sickchill.plugins.manager import plugin_manager

        load_first_party_clients()
        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_client_section(
            cfg,
            "sabnzbd",
            {"host": "http://sab:8080", "username": "sabuser", "password": "sabpass", "apikey": "sabkey"},
        )
        write_client_section(
            cfg,
            "nzbget",
            {"host": "nzb:6789", "username": "nzbuser", "password": "nzbpass", "priority": "50"},
        )
        plugin_manager._cfg = cfg
        plugin_manager.discover()
        plugin_manager._instances.clear()

        sab = plugin_manager.get(PluginKind.CLIENT, "sabnzbd")
        nzb = plugin_manager.get(PluginKind.CLIENT, "nzbget")
        self.assertIsNotNone(sab)
        self.assertIsNotNone(nzb)

        # Stale empty ctx + prior good settings
        sab.ctx._data.clear()
        nzb.ctx._data.clear()
        sc_settings.SAB_USERNAME = "keep-sab"
        sc_settings.SAB_APIKEY = "keep-key"
        sc_settings.SAB_HOST = "http://keep-sab"
        sc_settings.NZBGET_USERNAME = "keep-nzb"
        sc_settings.NZBGET_HOST = "keep-nzb-host"
        sc_settings.NZBGET_PASSWORD = "keep-nzb-pass"

        # Without reload this would blank; with reload CLIENTS wins
        sab._sync_settings()
        nzb._sync_settings()
        self.assertEqual(sc_settings.SAB_USERNAME, "sabuser")
        self.assertEqual(sc_settings.SAB_APIKEY, "sabkey")
        self.assertEqual(sc_settings.SAB_HOST, "http://sab:8080")
        self.assertEqual(sc_settings.NZBGET_USERNAME, "nzbuser")
        self.assertEqual(sc_settings.NZBGET_HOST, "nzb:6789")
        self.assertEqual(sc_settings.NZBGET_PASSWORD, "nzbpass")

        # If CLIENTS section missing keys, must not wipe existing settings
        write_client_section(cfg, "sabnzbd", {})
        write_client_section(cfg, "nzbget", {})
        sab.ctx._data.clear()
        nzb.ctx._data.clear()
        sab._sync_settings()
        nzb._sync_settings()
        self.assertEqual(sc_settings.SAB_USERNAME, "sabuser")
        self.assertEqual(sc_settings.NZBGET_USERNAME, "nzbuser")

    def test_sync_and_write_clients_roundtrip(self):
        from sickchill import settings as sc_settings

        cfg = ConfigObj()
        cfg.indent_type = "  "
        write_client_section(
            cfg,
            "transmission",
            {
                "host": "http://localhost:9091",
                "username": "u",
                "password": "p",
                "path": "/dl",
                "path_incomplete": "",
                "label": "tv",
                "label_anime": "",
                "paused": False,
                "seed_time": 0,
                "verify_cert": False,
                "rpcurl": "transmission",
                "high_bandwidth": False,
            },
        )
        write_client_section(cfg, "blackhole", {"nzb_dir": "/nzb", "torrent_dir": "/tor"})
        write_client_section(
            cfg,
            "sabnzbd",
            {
                "host": "http://sab",
                "username": "s",
                "password": "",
                "apikey": "k",
                "category": "tv",
                "category_backlog": "tv",
                "category_anime": "anime",
                "category_anime_backlog": "anime",
                "forced": False,
            },
        )
        write_client_section(
            cfg,
            "nzbget",
            {
                "host": "nzb:6789",
                "username": "nzbget",
                "password": "x",
                "category": "tv",
                "category_backlog": "tv",
                "category_anime": "anime",
                "category_anime_backlog": "anime",
                "use_https": False,
                "priority": 100,
            },
        )

        sc_settings.TORRENT_METHOD = "transmission"
        sc_settings.NZB_METHOD = "sabnzbd"
        sync_clients_from_settings(cfg)
        self.assertEqual(sc_settings.TORRENT_HOST, "http://localhost:9091")
        self.assertEqual(sc_settings.NZB_DIR, "/nzb")
        self.assertEqual(sc_settings.TORRENT_DIR, "/tor")
        self.assertEqual(sc_settings.SAB_HOST, "http://sab")
        self.assertEqual(sc_settings.NZBGET_HOST, "nzb:6789")

        out = ConfigObj()
        out.indent_type = "  "
        out["TORRENT"] = {"torrent_host": "should-be-removed"}
        out["Blackhole"] = {"nzb_dir": "old"}
        write_clients_to_cfg(out)
        self.assertNotIn("TORRENT", out)
        self.assertNotIn("Blackhole", out)
        self.assertEqual(read_client_section(out, "transmission").get("host"), "http://localhost:9091")
        self.assertEqual(read_client_section(out, "blackhole").get("nzb_dir"), "/nzb")
