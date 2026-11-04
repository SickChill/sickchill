"""%RG must follow the new release when replacing an existing episode file."""

from __future__ import annotations

from sickchill.tv import TVEpisode, TVShow
from tests import conftest


class TestReplaceReleaseGroupNaming(conftest.SickChillTestDBCase):
    """pretty_name/naming_pattern must not pin %RG from the file being replaced."""

    def setUp(self):
        super().setUp()
        self.show = TVShow(1, 1, "en")
        self.show.name = "Show Name"
        self.show.save_to_db()

        self.episode = TVEpisode(self.show, 1, 1)
        self.episode.name = "Pilot"
        self.episode.release_name = ""
        self.episode.release_group = ""
        self.episode._release_group = ""
        self.episode.location = "/library/Show.Name.S01E01.1080p.WEB.DL.x265-MeGusta.mkv"

    def test_pretty_name_does_not_cache_location_release_group(self):
        """Logging pretty_name must not store the old file's group for later %RG."""
        _ = self.episode.pretty_name

        self.assertEqual(self.episode._release_group, "")
        self.assertEqual(self.episode.release_group, "")
        self.assertEqual(self.episode.replace_map()["%RG"], "MeGusta")

    def test_new_release_group_wins_after_pretty_name(self):
        """
        Post-process order: "Processing as" (pretty_name) runs before release_group is set.
        proper_path / %RG must use the incoming group, not the file being replaced.
        """
        _ = self.episode.pretty_name

        self.episode.release_name = "Show.Name.S01E01.1080p.WEB.DL.x265-cakes"
        self.episode.release_group = "cakes"

        self.assertEqual(self.episode.replace_map()["%RG"], "cakes")
        named = self.episode.naming_pattern("Season %0S/%SN - S%0SE%0E - %SQN-%RG")
        self.assertIn("-cakes", named)
        self.assertNotIn("MeGusta", named)
        self.assertEqual(self.episode.release_group, "cakes")
