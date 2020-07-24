from unittest import TestCase


class MakoTest(TestCase):

    """ Test entry point for Mako
    """

    def test_entry_point(self):
        import pkg_resources

        # if the entrypoint isn't there, just pass, as the tests can be run
        # without any setuptools install
        for impl in pkg_resources.iter_entry_points(
            "mako.cache", "dogpile.cache"
        ):
            impl.load()
