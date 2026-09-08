"""AniDB scene-exception refresh (ScudLee XML) — no UDP API."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch
from xml.etree import ElementTree

from sickchill import settings
from sickchill.adba import aniDBfileInfo as anidb_files
from sickchill.oldbeard import scene_exceptions


def _write_map_xml(path: Path, entries: list[tuple[str, str, str]]) -> None:
    root = ElementTree.Element("anime-list")
    for anidb, tvdb, name in entries:
        anime = ElementTree.SubElement(root, "anime", anidbid=anidb, tvdbid=tvdb)
        ElementTree.SubElement(anime, "name").text = name
    ElementTree.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def _write_titles_xml(path: Path, entries: list[tuple[str, str]]) -> None:
    root = ElementTree.Element("animetitles")
    for aid, main_name in entries:
        anime = ElementTree.SubElement(root, "anime", aid=aid)
        title = ElementTree.SubElement(anime, "title", type="main")
        title.set("{http://www.w3.org/XML/1998/namespace}lang", "x-jat")
        title.text = main_name
    ElementTree.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


class DownloadFileSafetyTests(unittest.TestCase):
    def test_failed_download_keeps_existing_file(self):
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "anime-list.xml"
            target.write_text("<anime-list/>", encoding="utf-8")

            with patch("sickchill.adba.aniDBfileInfo.requests.get", side_effect=anidb_files.requests.exceptions.RequestException("boom")):
                self.assertFalse(anidb_files.download_file("https://example.test/x.xml", target))

            self.assertTrue(target.is_file())
            self.assertEqual(target.read_text(encoding="utf-8"), "<anime-list/>")
            self.assertFalse(list(Path(tmp).glob("*.tmp")))


class AnidbExceptionsGeneratorTests(unittest.TestCase):
    def setUp(self):
        self._saved = {
            "show_list": settings.show_list,
            "CACHE_DIR": settings.CACHE_DIR,
            "stopping": settings.stopping,
            "restarting": settings.restarting,
        }
        # Other tests can leave these True and abort the generator early (CI flake).
        settings.stopping = False
        settings.restarting = False

        self._tmp = TemporaryDirectory()
        self.cache_root = Path(self._tmp.name)
        self.anime_dir = self.cache_root / "anime"
        self.anime_dir.mkdir()
        settings.CACHE_DIR = str(self.cache_root)

        _write_map_xml(
            self.anime_dir / "anime-list.xml",
            [
                ("12385", "329820", "Isekai Shokudou"),
                ("1", "72025", "Seikai no Monshou"),
            ],
        )
        _write_titles_xml(
            self.anime_dir / "animetitles.xml",
            [
                ("12385", "Isekai Shokudou"),
                ("1", "Seikai no Monshou"),
            ],
        )

    def tearDown(self):
        settings.show_list = self._saved["show_list"]
        settings.CACHE_DIR = self._saved["CACHE_DIR"]
        settings.stopping = self._saved["stopping"]
        settings.restarting = self._saved["restarting"]
        self._tmp.cleanup()

    def _show(self, name: str, indexerid: int, is_anime: bool = True, indexer: int = 1):
        show = MagicMock()
        show.name = name
        show.indexerid = indexerid
        show.is_anime = is_anime
        show.indexer = indexer
        return show

    @patch("sickchill.oldbeard.scene_exceptions.should_refresh", return_value=True)
    @patch("sickchill.oldbeard.scene_exceptions.set_last_refresh")
    def test_yields_anidb_main_name_when_different(self, set_refresh, _should):
        settings.show_list = [
            self._show("Restaurant to Another World", 329820),
            self._show("4 Cut Hero", 462598),  # unmapped → skipped, not raised
            self._show("Not Anime", 1, is_anime=False),
        ]

        results = list(scene_exceptions._anidb_exceptions_generator())
        self.assertEqual(results, [(329820, "Isekai Shokudou", -1)])
        set_refresh.assert_called_once_with("anidb")

    @patch("sickchill.adba.aniDBfileInfo.get_anime_titles_xml", return_value=False)
    @patch("sickchill.adba.aniDBfileInfo.get_anime_list_xml", return_value=False)
    @patch("sickchill.oldbeard.scene_exceptions.should_refresh", return_value=True)
    @patch("sickchill.oldbeard.scene_exceptions.set_last_refresh")
    def test_skips_when_xml_missing(self, set_refresh, _should, _list_dl, _titles_dl):
        for path in self.anime_dir.glob("*.xml"):
            path.unlink()
        settings.show_list = [self._show("Restaurant to Another World", 329820)]

        self.assertEqual(list(scene_exceptions._anidb_exceptions_generator()), [])
        set_refresh.assert_not_called()


if __name__ == "__main__":
    unittest.main()
