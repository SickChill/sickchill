# coding=utf-8
"""
Test sickbeard.config's classes and methods

Classes:
    ConfigMigrator
        migrate_config
        _migrate_v1
        _name_to_pattern
        _migrate_v2
        _migrate_v3
        _migrate_v4
        _migrate_v5
        _migrate_v6
        _migrate_v7

Methods
    change_https_cert
    change_https_key
    change_log_dir
    change_nzb_dir
    change_torrent_dir
    change_tv_download_dir
    change_postprocessor_frequency
    change_daily_search_frequency
    change_backlog_frequency
    change_update_frequency
    change_showupdate_hour
    change_subtitle_finder_frequency
    change_VERSION_NOTIFY
    change_download_propers
    change_use_trakt
    change_use_subtitles
    change_process_automatically
    CheckSection
    checkbox_to_value
    clean_host
    clean_hosts
    clean_url
    minimax
    check_setting_int
    check_setting_float
    check_setting_str
"""

# pylint: disable=line-too-long

import logging
import os.path
import sys
import unittest
from collections import namedtuple

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import config


class ConfigTestBasic(unittest.TestCase):
    """
    Test basic methods in sickbeard.config
    """
    @unittest.skip('Test not implemented')
    def test_check_section(self):
        """
        Test check_section
        """
        pass

    @unittest.skip('Test not implemented')
    def test_checkbox_to_value(self):
        """
        Test checkbox_to_value
        """
        pass

    @unittest.skip('Test not implemented')
    def test_clean_host(self):
        """
        Test clean_host
        """
        pass

    @unittest.skip('Test not implemented')
    def test_clean_hosts(self):
        """
        Test clean_hosts
        """
        pass

    def test_clean_url(self):
        """
        Test cleaning of urls
        """
        log = logging.getLogger(__name__)
        test = namedtuple('test', 'expected_result dirty clean')

        url_tests = [
            test(True, "https://subdomain.domain.tld/endpoint", "https://subdomain.domain.tld/endpoint"),  # does not add a final /
            test(True, "http://www.example.com/folder/", "http://www.example.com/folder/"),  # does not remove the final /
            test(True, "google.com/xml.rpc", "http://google.com/xml.rpc"),  # add scheme if missing
            test(True, "google.com", "http://google.com/"),  # add scheme if missing and final / if its just the domain
            test(True, "scgi:///home/user/.config/path/socket", "scgi:///home/user/.config/path/socket"),  # scgi identified as scheme
            test(True, None, ''),  # None URL returns empty string
            test(False, "https://subdomain.domain.tld/endpoint", "http://subdomain.domain.tld/endpoint"),  # does not change schemes from https to http
            test(False, "http://subdomain.domain.tld/endpoint", "https://subdomain.domain.tld/endpoint"),  # ...or vice versa
            test(False, "google.com/xml.rpc", "google.com/xml.rpc"),  # scheme is always added
            test(False, "google.com", "https://google.com/"),  # does not default to https
            test(False, "http://www.example.com/folder/", "http://www.example.com/folder"),  # does not strip final /
            test(False, "scgi:///home/user/.config/path/socket", "scgi:///home/user/.config/path/socket/"),  # does not add a final /
            test(AttributeError, 1, 1),  # None URL returns empty string
        ]

        for test_url in url_tests:
            if issubclass(type(Exception), type(test_url.expected_result)):
                with self.assertRaises(test_url.expected_result):
                    self.assertEqual(config.clean_url(test_url.dirty), test_url.clean)
            elif test_url.expected_result is True:
                self.assertEqual(config.clean_url(test_url.dirty), test_url.clean)
            elif test_url.expected_result is False:
                self.assertNotEqual(config.clean_url(test_url.dirty), test_url.clean)
            else:
                log.error('Test not defined for %s', test_url)

    @unittest.skip('Test not implemented')
    def test_mini_max(self):
        """
        Test mini_max
        """
        pass

    @unittest.skip('Test not implemented')
    def test_check_setting_int(self):
        """
        Test check_setting_int
        """
        pass

    @unittest.skip('Test not implemented')
    def test_check_setting_float(self):
        """
        Test check_setting_float
        """
        pass

    @unittest.skip('Test not implemented')
    def test_check_setting_str(self):
        """
        Test check_setting_str
        """
        pass


class ConfigTestChanges(unittest.TestCase):
    """
    Test change methods in sickbeard.config
    """
    @unittest.skip('Test not implemented')
    def test_change_https_cert(self):
        """
        Test change_https_cert
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_https_key(self):
        """
        Test change_https_key
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_log_dir(self):
        """
        Test change_log_dir
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_nzb_dir(self):
        """
        Test change_nzb_dir
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_torrent_dir(self):
        """
        Test change_torrent_dir
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_tv_download_dir(self):
        """
        Test change_tv_download_dir
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_auto_pp_freq(self):
        """
        Test change_auto_pp_freq
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_daily_search_freq(self):
        """
        Test change_daily_search_freq
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_backlog_freq(self):
        """
        Test change_backlog_freq
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_update_freq(self):
        """
        Test change_update_freq
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_show_update_hour(self):
        """
        Test change_show_update_hour
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_sub_finder_freq(self):
        """
        Test change_sub_finder_freq
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_version_notify(self):
        """
        Test change_version_notify
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_download_propers(self):
        """
        Test change_download_propers
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_use_trakt(self):
        """
        Test change_use_trakt
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_use_subtitles(self):
        """
        Test change_use_subtitles
        """
        pass

    @unittest.skip('Test not implemented')
    def test_change_process_auto(self):
        """
        Test change_process_auto
        """
        pass


class ConfigTestMigrator(unittest.TestCase):
    """
    Test the sickbeard.config.ConfigMigrator class
    """
    @unittest.skip('Not yet implemented')
    def test_config_migrator(self):
        """
        Test config_migrator
        """
        pass


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestBasic)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestChanges)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestMigrator)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
