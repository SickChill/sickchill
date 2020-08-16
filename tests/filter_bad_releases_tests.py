import unittest

from sickchill import settings
from sickchill.oldbeard.show_name_helpers import filter_bad_releases
from sickchill.tv import TVShow as Show


class ReleaseWordFilterTests(unittest.TestCase):
    def setUp(self):
        settings.QUALITY_DEFAULT = 2
        self.show = Show(1, 1)
        settings.REQUIRE_WORDS = 'REQUIRED'
        settings.IGNORE_WORDS = 'IGNORED'

        # These are opposite of global, to prove they override
        self.show.rls_ignore_words = 'REQUIRED'
        self.show.rls_require_words = 'IGNORED'

    def test_global_only(self):
        self.assertFalse(filter_bad_releases('Release name that is IGNORED', False))
        self.assertTrue(filter_bad_releases('Release name that is REQUIRED', False))

        self.assertFalse(filter_bad_releases('Release name that is REQUIRED but contains IGNORED', False))

    def test_show_required_ignored_words(self):
        self.assertFalse(filter_bad_releases('Release name that is not REQUIRED', False, show=self.show))
        self.assertTrue(filter_bad_releases('Release name that is not IGNORED', False, show=self.show))

        self.assertFalse(filter_bad_releases('Release name that is not REQUIRED but contains IGNORED', False, show=self.show))

    def test_no_show_required_ignored_words(self):
        self.show.rls_ignore_words = ''
        self.show.rls_require_words = ''

        self.assertFalse(filter_bad_releases('Release name that is IGNORED', False, show=self.show))
        self.assertTrue(filter_bad_releases('Release name that is REQUIRED', False, show=self.show))

        self.assertFalse(filter_bad_releases('Release name that is REQUIRED but contains IGNORED', False, show=self.show))

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ReleaseWordFilterTests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
