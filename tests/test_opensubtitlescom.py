"""Tests for the OpenSubtitlesCom provider integration."""

import unittest

from sickchill import settings
from sickchill.oldbeard import subtitles as subtitle_module


class TestOpenSubtitlesComProvider(unittest.TestCase):
    """Test OpenSubtitlesCom provider registration and configuration."""

    def test_provider_registered(self):
        """opensubtitlescom should be registered in subliminal's provider manager."""
        self.assertIn("opensubtitlescom", subtitle_module.subliminal.provider_manager.names())

    def test_provider_url_exists(self):
        """opensubtitlescom should have a URL in PROVIDER_URLS."""
        self.assertIn("opensubtitlescom", subtitle_module.PROVIDER_URLS)
        self.assertEqual(subtitle_module.PROVIDER_URLS["opensubtitlescom"], "https://www.opensubtitles.com")

    def test_legacy_opensubtitles_url_is_org(self):
        """Legacy opensubtitles should point to .org (XML-RPC API)."""
        self.assertEqual(subtitle_module.PROVIDER_URLS["opensubtitles"], "https://www.opensubtitles.org")

    def test_settings_attributes_exist(self):
        """Settings module should have OPENSUBTITLESCOM_USER and OPENSUBTITLESCOM_PASS."""
        self.assertTrue(hasattr(settings, "OPENSUBTITLESCOM_USER"))
        self.assertTrue(hasattr(settings, "OPENSUBTITLESCOM_PASS"))

    def test_provider_pool_includes_credentials(self):
        """SubtitleProviderPool should pass opensubtitlescom credentials to subliminal."""
        saved_user = settings.OPENSUBTITLESCOM_USER
        saved_pass = settings.OPENSUBTITLESCOM_PASS
        saved_services = settings.SUBTITLES_SERVICES_LIST
        saved_enabled = settings.SUBTITLES_SERVICES_ENABLED
        saved_instance = subtitle_module.SubtitleProviderPool._instance
        saved_creation = subtitle_module.SubtitleProviderPool._creation

        settings.OPENSUBTITLESCOM_USER = "testuser"
        settings.OPENSUBTITLESCOM_PASS = "testpass"  # noqa: S105
        settings.SUBTITLES_SERVICES_LIST = ["opensubtitlescom"]
        settings.SUBTITLES_SERVICES_ENABLED = [1]
        subtitle_module.SubtitleProviderPool._instance = None
        subtitle_module.SubtitleProviderPool._creation = None

        try:
            subtitle_module.SubtitleProviderPool()
            provider_configs = subtitle_module.SubtitleProviderPool._instance.provider_configs
            self.assertIn("opensubtitlescom", provider_configs)
            self.assertEqual(provider_configs["opensubtitlescom"]["username"], "testuser")
            self.assertEqual(provider_configs["opensubtitlescom"]["password"], "testpass")  # noqa: S105
        finally:
            settings.OPENSUBTITLESCOM_USER = saved_user
            settings.OPENSUBTITLESCOM_PASS = saved_pass
            settings.SUBTITLES_SERVICES_LIST = saved_services
            settings.SUBTITLES_SERVICES_ENABLED = saved_enabled
            subtitle_module.SubtitleProviderPool._instance = saved_instance
            subtitle_module.SubtitleProviderPool._creation = saved_creation
