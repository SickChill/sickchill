"""Tests for forceAutoPostProcess redirect safety (open-redirect hardening)."""

from __future__ import annotations

import unittest

from sickchill import settings
from sickchill.helper.common import is_safe_internal_redirect, resolve_safe_redirect


class TestIsSafeInternalRedirect(unittest.TestCase):
    def test_accepts_same_site_paths(self):
        self.assertTrue(is_safe_internal_redirect("/home/"))
        self.assertTrue(is_safe_internal_redirect("/manage/manageSearches/"))
        self.assertTrue(is_safe_internal_redirect("/home/?foo=bar"))

    def test_rejects_protocol_relative_and_schemes(self):
        self.assertFalse(is_safe_internal_redirect("//attacker.example"))
        self.assertFalse(is_safe_internal_redirect("https://attacker.example/"))
        self.assertFalse(is_safe_internal_redirect("http://attacker.example/path"))
        self.assertFalse(is_safe_internal_redirect("javascript:alert(1)"))

    def test_rejects_encoded_backslash_payload_independent_of_web_root(self):
        """Browser-level payload: next=/%5C%5Cattacker.example with WEB_ROOT set."""
        for web_root in ("", "/sickchill", "/sc"):
            with self.subTest(WEB_ROOT=web_root):
                settings.WEB_ROOT = web_root
                # Encoded form (as in the query string before/after decode rounds)
                self.assertFalse(is_safe_internal_redirect("/%5C%5Cattacker.example"))
                # Tornado-decoded form of the same payload
                self.assertFalse(is_safe_internal_redirect("/\\\\attacker.example"))
                self.assertFalse(is_safe_internal_redirect("/\\attacker.example"))
                # Valid paths still accepted under any WEB_ROOT
                self.assertTrue(is_safe_internal_redirect("/home/"))

    def test_rejects_empty_and_relative(self):
        self.assertFalse(is_safe_internal_redirect(None))
        self.assertFalse(is_safe_internal_redirect(""))
        self.assertFalse(is_safe_internal_redirect("home/"))
        self.assertFalse(is_safe_internal_redirect("./home/"))


class TestResolveSafeRedirect(unittest.TestCase):
    """Handler-level decision: evil next= must not be used; falls back to default page."""

    def test_encoded_backslash_next_ignored_with_web_root(self):
        settings.WEB_ROOT = "/sickchill"
        # Decoded equivalent of /%5C%5Cattacker.example
        target = resolve_safe_redirect("/\\\\attacker.example", "http://localhost:8081/home/", "localhost:8081", "home")
        self.assertEqual(target, "/home/")
        self.assertNotIn("attacker", target)
        self.assertNotIn("\\", target)

    def test_encoded_string_form_also_ignored(self):
        settings.WEB_ROOT = "/sickchill"
        target = resolve_safe_redirect("/%5C%5Cattacker.example", "", "localhost:8081", "home")
        self.assertEqual(target, "/home/")

    def test_valid_next_preserved(self):
        settings.WEB_ROOT = "/sickchill"
        self.assertEqual(
            resolve_safe_redirect("/manage/manageSearches/", "http://localhost:8081/other/", "localhost:8081", "home"),
            "/manage/manageSearches/",
        )


if __name__ == "__main__":
    unittest.main()
