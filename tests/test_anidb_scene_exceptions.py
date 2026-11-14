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


def _write_map_xml(path: Path, entries: list[tuple]) -> None:
    root = ElementTree.Element("anime-list")
    for entry in entries:
        anidb, tvdb, name = entry[0], entry[1], entry[2]
        attrs = {"anidbid": anidb, "tvdbid": tvdb}
        if len(entry) > 3 and entry[3] is not None:
            attrs["defaulttvdbseason"] = str(entry[3])
        anime = ElementTree.SubElement(root, "anime", **attrs)
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
        self._saved_show_list = settings.show_list
        self._saved_cache_dir = settings.CACHE_DIR
        self._saved_stopping = settings.stopping
        self._saved_restarting = settings.restarting
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
                ("12385", "329820", "Isekai Shokudou", "1"),
                ("1", "72025", "Seikai no Monshou", "1"),
                ("4", "72025", "Seikai no Senki", "2"),
            ],
        )
        _write_titles_xml(
            self.anime_dir / "animetitles.xml",
            [
                ("12385", "Isekai Shokudou"),
                ("1", "Seikai no Monshou"),
                ("4", "Seikai no Senki"),
            ],
        )

    def tearDown(self):
        settings.show_list = self._saved_show_list
        settings.CACHE_DIR = self._saved_cache_dir
        settings.stopping = self._saved_stopping
        settings.restarting = self._saved_restarting
        self._tmp.cleanup()

    def _show(self, name: str, indexerid: int, is_anime: bool = True, indexer: int = 1, default_tvdb_season=None, episodes=None):
        show = MagicMock()
        show.name = name
        show.indexerid = indexerid
        show.is_anime = is_anime
        show.indexer = indexer
        show.default_tvdb_season = default_tvdb_season
        show.episodes = episodes if episodes is not None else {}
        return show

    @patch("sickchill.oldbeard.scene_exceptions.should_refresh", return_value=True)
    @patch("sickchill.oldbeard.scene_exceptions.set_last_refresh")
    def test_tvdb_72025_selects_season_specific_anidb_title(self, set_refresh, _should):
        # Whole series: both AniDB titles, tagged with defaulttvdbseason
        settings.show_list = [self._show("Crest of the Stars", 72025)]
        results = list(scene_exceptions._anidb_exceptions_generator())
        self.assertEqual(
            sorted(results),
            [
                (72025, "Seikai no Monshou", 1),
                (72025, "Seikai no Senki", 2),
            ],
        )

        # Season-2-only show must not first-wins onto aid 1
        settings.show_list = [self._show("Banner of the Stars", 72025, default_tvdb_season=2)]
        results = list(scene_exceptions._anidb_exceptions_generator())
        self.assertEqual(results, [(72025, "Seikai no Senki", 2)])
        set_refresh.assert_called_with("anidb")


if __name__ == "__main__":
    unittest.main()
