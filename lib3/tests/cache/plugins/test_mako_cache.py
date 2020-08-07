from unittest import TestCase

from mako.cache import register_plugin
from mako.template import Template
import mock
import pytest

from .. import eq_


try:
    import mako  # noqa
except ImportError:
    raise pytest.skip("this test suite requires mako templates")

register_plugin(
    "dogpile.cache", "dogpile.cache.plugins.mako_cache", "MakoPlugin"
)


class TestMakoPlugin(TestCase):
    def _mock_fixture(self):
        reg = mock.MagicMock()
        reg.get_or_create.return_value = "hello world"
        my_regions = {"myregion": reg}
        return (
            {
                "cache_impl": "dogpile.cache",
                "cache_args": {"regions": my_regions},
            },
            reg,
        )

    def test_basic(self):
        kw, reg = self._mock_fixture()
        t = Template('<%page cached="True" cache_region="myregion"/>hi', **kw)
        t.render()
        eq_(reg.get_or_create.call_count, 1)

    def test_timeout(self):
        kw, reg = self._mock_fixture()
        t = Template(
            """
                <%def name="mydef()" cached="True" cache_region="myregion"
                        cache_timeout="20">
                    some content
                </%def>
                ${mydef()}
                """,
            **kw
        )
        t.render()
        eq_(reg.get_or_create.call_args[1], {"expiration_time": 20})
