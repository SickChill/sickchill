import logging

import pytest
from packaging import version as packaging_version

from sickchill import settings
from sickchill.update_manager import pip


@pytest.fixture()
def updater(caplog):
    with caplog.at_level(logging.WARNING, logger="root"):
        caplog.set_level(logging.DEBUG, logger="sickchill")
        caplog.set_level(logging.WARNING, logger="cacheyou")
        caplog.set_level(logging.WARNING, logger="urllib3")
        fixture = pip.PipUpdateManager()
        fixture.version_text = "2022.9.14"
        yield fixture


class TestPipUpdateManager:
    def test_get_current_version(self, updater):
        assert updater.get_current_version() == packaging_version.parse(updater.version_text)

    def test_get_clean_version(self, updater):
        assert updater.get_clean_version() == updater.version_text
        assert updater.get_clean_version(use_version=packaging_version.parse("2022.8.30")) == "2022.8.30"

    def test_get_newest_version(self, updater):
        assert updater.get_newest_version() == packaging_version.parse(updater.newest_version_text)

    def test_get_version_delta(self, updater):
        assert updater.get_current_version() == packaging_version.parse("2022.9.14")

        assert updater.get_version_delta().startswith("Major:")

        updater.version_text = updater.get_clean_version(use_version=updater.get_newest_version())
        assert updater.get_version_delta() == 0

    def test_set_newest_text(self, updater):
        assert updater.need_update()
        updater.set_newest_text()
        assert settings.SITE_MESSAGES

    def test_need_update(self, updater):
        assert updater.need_update()

        updater.version_text = updater.get_clean_version(use_version=updater.get_newest_version())
        assert not updater.need_update()

    def test_update(self, updater):
        assert updater.update()

    def test_pip_install(self, updater):
        assert updater.pip_install("sickchill")
