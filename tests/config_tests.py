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
    change_sickrage_background
    change_log_dir
    change_nzb_dir
    change_torrent_dir
    change_tv_download_dir
    change_unpack_dir
    change_postprocessor_frequency
    change_daily_search_frequency
    change_backlog_frequency
    change_update_frequency
    change_showupdate_hour
    change_subtitle_finder_frequency
    change_version_notify
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
    check_setting_bool
"""

# pylint: disable=line-too-long

import logging
import os.path
import sys
import unittest
from collections import namedtuple

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickbeard import config, scheduler
from configobj import ConfigObj
import sickbeard

class ConfigTestBasic(unittest.TestCase):
    """
    Test basic methods in sickbeard.config
    """

    def test_check_section(self):
        """
        Test CheckSection
        """
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        self.assertFalse(config.CheckSection(CFG, 'General'))
        self.assertTrue(config.CheckSection(CFG, 'General'))

    def test_checkbox_to_value(self):
        """
        Test checkbox_to_value
        """
        self.assertTrue(config.checkbox_to_value(1))
        self.assertTrue(config.checkbox_to_value(['option', 'True']))
        self.assertEqual(config.checkbox_to_value('0', 'yes', 'no'), 'no')

    def test_clean_host(self):
        """
        Test clean_host
        """
        self.assertEqual(config.clean_host('http://127.0.0.1:8080'), '127.0.0.1:8080')
        self.assertEqual(config.clean_host('https://mail.google.com/mail'), 'mail.google.com')
        self.assertEqual(config.clean_host('http://localhost:8081/home/displayShow?show=80379#season-10'),
                         'localhost:8081')
        self.assertEqual(config.clean_host('http://testme.co.uk', 9000), 'testme.co.uk:9000')  # default port
        self.assertEqual(config.clean_host('www.google.com/search'), 'www.google.com')
        self.assertEqual(config.clean_host(''), '') # empty host

    def test_clean_hosts(self):
        """
        Test clean_hosts
        """
        dirty_hosts = 'http://127.0.0.1:8080,https://mail.google.com/mail,' \
                      'http://localhost:8081/home/displayShow?show=80379#season-10,' \
                      'www.google.com/search,'
        clean_result = '127.0.0.1:8080,mail.google.com:5050,localhost:8081,www.google.com:5050'
        self.assertEqual(config.clean_hosts(dirty_hosts, '5050'), clean_result)

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

    def test_mini_max(self):
        """
        Test minimax
        """

        self.assertEqual(config.minimax('100', default=50, low=50, high=200), 100)
        self.assertEqual(config.minimax('25', default=50, low=50, high=200), 50)
        self.assertEqual(config.minimax('250', default=50, low=50, high=200), 200)

    def test_check_setting_int(self):
        """
        Test check_setting_int
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.CheckSection(CFG, 'General')
        CFG['General']['indexer_timeout'] = 60
        CFG['General']['use_icacls'] = 'True'
        CFG['General']['use_nzbs'] = 'False'
        CFG['General']['status_default'] = None
        # normal
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 30), 60)
        # true/false => int
        self.assertEqual(config.check_setting_int(CFG, 'General', 'use_icacls', 1), 1)
        self.assertEqual(config.check_setting_int(CFG, 'General', 'use_nzbs', 0), 0)
        # None value type + silent off
        self.assertEqual(config.check_setting_int(CFG, 'General', 'status_default', 5, silent=False), 5)
        # unmatched section
        self.assertEqual(config.check_setting_int(CFG, 'Subtitles', 'subtitles_finder_frequency', 1), 1)

    def test_check_setting_float(self):
        """
        Test check_setting_float
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.CheckSection(CFG, 'General')
        CFG['General']['fanart_background_opacity'] = 0.2
        CFG['General']['log_size'] = None
        # normal
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.4), 0.2)
        # None value type + silent off
        self.assertEqual(config.check_setting_float(CFG, 'General', 'log_size', 10.0, silent=False), 10.0)
        # unmatched section
        self.assertEqual(config.check_setting_float(CFG, 'Kodi', 'log_size', 2.5), 2.5)

    def test_check_setting_str(self):
        """
        Test check_setting_str
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.CheckSection(CFG, 'General')
        CFG['General']['process_method'] = "copy"
        CFG['General']['git_password'] = "SFa342FHb_"
        CFG['General']['extra_scripts'] = None
        # normal
        self.assertEqual(config.check_setting_str(CFG, 'General', 'process_method', 'move'), 'copy')
        self.assertEqual(config.check_setting_str(CFG, 'General', 'git_password', '', silent=False, censor_log=True),
                         'SFa342FHb_')
        # None value type
        self.assertEqual(config.check_setting_str(CFG, 'General', 'extra_scripts', ''), '')
        # unmatched section
        self.assertEqual(config.check_setting_str(CFG, 'Subtitles', 'subtitles_languages', 'eng'), 'eng')

    def test_check_setting_bool(self):
        """
        Test check_setting_bool
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.CheckSection(CFG, 'General')
        CFG['General']['debug'] = True
        CFG['General']['season_folders_default'] = False
        # normal
        self.assertTrue(config.check_setting_bool(CFG, 'General', 'debug'))
        self.assertFalse(config.check_setting_bool(CFG, 'General', 'season_folders_default', def_val=True))
        # unmatched item
        self.assertTrue(config.check_setting_bool(CFG, 'General', 'git_reset', def_val=True))
        # unmatched section
        self.assertFalse(config.check_setting_bool(CFG, 'Subtitles', 'use_subtitles', def_val=False))
        # wrong def_val type, silent = off
        self.assertTrue(config.check_setting_bool(
            CFG, 'General', 'debug', def_val=0, silent=False))


class ConfigTestChanges(unittest.TestCase):
    """
    Test change methods in sickbeard.config
    """

    def test_change_https_cert(self):
        """
        Test change_https_cert
        """
        sickbeard.HTTPS_CERT = 'server.crt' # Initialize
        self.assertTrue(config.change_https_cert(''))
        self.assertTrue(config.change_https_cert('server.crt'))
        self.assertFalse(config.change_https_cert('XYZ:\\server.crt'))
        sickbeard.HTTPS_CERT = ''

    def test_change_https_key(self):
        """
        Test change_https_key
        """
        sickbeard.HTTPS_KEY = 'server.key'  # Initialize
        self.assertTrue(config.change_https_key(''))
        self.assertTrue(config.change_https_key('server.key'))
        self.assertFalse(config.change_https_key('XYZ:\\server.key'))
        sickbeard.HTTPS_KEY = ''

    def test_change_sickrage_background(self):
        """
        Test change_sickrage_background
        """
        sickbeard.SICKRAGE_BACKGROUND_PATH = ''  # Initialize
        self.assertTrue(config.change_sickrage_background(__file__))
        self.assertFalse(config.change_sickrage_background('not_real.jpg'))
        self.assertTrue(config.change_sickrage_background(''))

    def test_change_log_dir(self):
        """
        Test change_log_dir
        """
        sickbeard.DATA_DIR = os.path.dirname(__file__)
        sickbeard.ACTUAL_LOG_DIR = ''
        sickbeard.LOG_DIR = os.path.join(sickbeard.DATA_DIR, sickbeard.ACTUAL_LOG_DIR)
        sickbeard.WEB_LOG = False

        self.assertFalse(config.change_log_dir('XYZ:\\Logs', True))
        self.assertTrue(config.change_log_dir('Logs', True))

    def test_change_nzb_dir(self):
        """
        Test change_nzb_dir
        """
        sickbeard.NZB_DIR = ''
        self.assertTrue(config.change_nzb_dir('cache'))
        self.assertFalse(config.change_nzb_dir('XYZ:\\NZB_Downloads'))
        self.assertTrue(config.change_nzb_dir(''))

    def test_change_torrent_dir(self):
        """
        Test change_torrent_dir
        """
        sickbeard.TORRENT_DIR = ''
        self.assertTrue(config.change_torrent_dir('cache'))
        self.assertFalse(config.change_torrent_dir('XYZ:\\Downloads'))
        self.assertTrue(config.change_torrent_dir(''))

    def test_change_tv_download_dir(self):
        """
        Test change_tv_download_dir
        """
        sickbeard.TV_DOWNLOAD_DIR = ''
        self.assertTrue(config.change_tv_download_dir('cache'))
        self.assertFalse(config.change_tv_download_dir('XYZ:\\Downloads\\Completed'))
        self.assertTrue(config.change_tv_download_dir(''))

    def test_change_unpack_dir(self):
        """
        Test change_unpack_dir
        """
        sickbeard.TV_DOWNLOAD_DIR = ''
        self.assertTrue(config.change_unpack_dir('cache'))
        self.assertFalse(config.change_unpack_dir('XYZ:\\Extract'))
        self.assertTrue(config.change_unpack_dir(''))

    def test_change_auto_pp_freq(self):
        """
        Test change_postprocessor_frequency
        """
        sickbeard.autoPostProcessorScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_postprocessor_frequency(0)
        self.assertEqual(sickbeard.AUTOPOSTPROCESSOR_FREQUENCY, sickbeard.MIN_AUTOPOSTPROCESSOR_FREQUENCY)
        config.change_postprocessor_frequency('s')
        self.assertEqual(sickbeard.AUTOPOSTPROCESSOR_FREQUENCY, sickbeard.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY)
        config.change_postprocessor_frequency(60)
        self.assertEqual(sickbeard.AUTOPOSTPROCESSOR_FREQUENCY, 60)

    def test_change_daily_search_freq(self):
        """
        Test change_daily_search_frequency
        """
        sickbeard.dailySearchScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_daily_search_frequency(0)
        self.assertEqual(sickbeard.DAILYSEARCH_FREQUENCY, sickbeard.MIN_DAILYSEARCH_FREQUENCY)
        config.change_daily_search_frequency('s')
        self.assertEqual(sickbeard.DAILYSEARCH_FREQUENCY, sickbeard.DEFAULT_DAILYSEARCH_FREQUENCY)
        config.change_daily_search_frequency(60)
        self.assertEqual(sickbeard.DAILYSEARCH_FREQUENCY, 60)

    def test_change_backlog_freq(self):
        """
        Test change_backlog_frequency
        """
        sickbeard.backlogSearchScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickbeard.DAILYSEARCH_FREQUENCY = sickbeard.DEFAULT_DAILYSEARCH_FREQUENCY # needed

        config.change_backlog_frequency(0)
        self.assertEqual(sickbeard.BACKLOG_FREQUENCY, sickbeard.MIN_BACKLOG_FREQUENCY)
        config.change_backlog_frequency('s')
        self.assertEqual(sickbeard.BACKLOG_FREQUENCY, sickbeard.MIN_BACKLOG_FREQUENCY)
        config.change_backlog_frequency(1440)
        self.assertEqual(sickbeard.BACKLOG_FREQUENCY, 1440)

    def test_change_update_freq(self):
        """
        Test change_update_frequency
        """
        sickbeard.versionCheckScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_update_frequency(0)
        self.assertEqual(sickbeard.UPDATE_FREQUENCY, sickbeard.MIN_UPDATE_FREQUENCY)
        config.change_update_frequency('s')
        self.assertEqual(sickbeard.UPDATE_FREQUENCY, sickbeard.DEFAULT_UPDATE_FREQUENCY)
        config.change_update_frequency(60)
        self.assertEqual(sickbeard.UPDATE_FREQUENCY, 60)

    def test_change_show_update_hour(self):
        """
        Test change_showupdate_hour
        """
        sickbeard.showUpdateScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_showupdate_hour(-2)
        self.assertEqual(sickbeard.SHOWUPDATE_HOUR, 0)
        config.change_showupdate_hour('s')
        self.assertEqual(sickbeard.SHOWUPDATE_HOUR, sickbeard.DEFAULT_SHOWUPDATE_HOUR)
        config.change_showupdate_hour(60)
        self.assertEqual(sickbeard.SHOWUPDATE_HOUR, 0)
        config.change_showupdate_hour(12)
        self.assertEqual(sickbeard.SHOWUPDATE_HOUR, 12)

    def test_change_sub_finder_freq(self):
        """
        Test change_subtitle_finder_frequency
        """
        config.change_subtitle_finder_frequency('')
        self.assertEqual(sickbeard.SUBTITLES_FINDER_FREQUENCY, 1)
        config.change_subtitle_finder_frequency('s')
        self.assertEqual(sickbeard.SUBTITLES_FINDER_FREQUENCY, 1)
        config.change_subtitle_finder_frequency(8)
        self.assertEqual(sickbeard.SUBTITLES_FINDER_FREQUENCY, 8)

    def test_change_version_notify(self):
        """
        Test change_version_notify
        """
        class dummy_action(object): # needed for *scheduler.action.forceRun()
            def __init__(self):
                self.amActive = False

        sickbeard.versionCheckScheduler = scheduler.Scheduler(dummy_action()) # dummy
        sickbeard.VERSION_NOTIFY = True

        config.change_version_notify(True) # no change
        self.assertTrue(sickbeard.VERSION_NOTIFY)
        config.change_version_notify('stop') # = defaults to False
        self.assertFalse(sickbeard.VERSION_NOTIFY and sickbeard.versionCheckScheduler.enable)
        config.change_version_notify('on')
        self.assertTrue(sickbeard.VERSION_NOTIFY and sickbeard.versionCheckScheduler.enable)

    def test_change_download_propers(self):
        """
        Test change_download_propers
        """
        sickbeard.properFinderScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickbeard.DOWNLOAD_PROPERS = True

        config.change_download_propers(True) # no change
        self.assertTrue(sickbeard.DOWNLOAD_PROPERS)
        config.change_download_propers('stop') # = defaults to False
        self.assertFalse(sickbeard.DOWNLOAD_PROPERS and sickbeard.properFinderScheduler.enable)
        config.change_download_propers('on')
        self.assertTrue(sickbeard.DOWNLOAD_PROPERS and sickbeard.properFinderScheduler.enable)

    def test_change_use_trakt(self):
        """
        Test change_use_trakt
        """
        sickbeard.traktCheckerScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickbeard.USE_TRAKT = True

        config.change_use_trakt(True) # no change
        self.assertTrue(sickbeard.USE_TRAKT)
        config.change_use_trakt('stop') # = defaults to False
        self.assertFalse(sickbeard.USE_TRAKT and sickbeard.traktCheckerScheduler.enable)
        config.change_use_trakt('on')
        self.assertTrue(sickbeard.USE_TRAKT and sickbeard.traktCheckerScheduler.enable)

    def test_change_use_subtitles(self):
        """
        Test change_use_subtitles
        """
        sickbeard.subtitlesFinderScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickbeard.USE_SUBTITLES = True

        config.change_use_subtitles(True) # no change
        self.assertTrue(sickbeard.USE_SUBTITLES)
        config.change_use_subtitles('stop') # = defaults to False
        self.assertFalse(sickbeard.USE_SUBTITLES and sickbeard.subtitlesFinderScheduler.enable)
        config.change_use_subtitles('on')
        self.assertTrue(sickbeard.USE_SUBTITLES and sickbeard.subtitlesFinderScheduler.enable)

    def test_change_process_auto(self):
        """
        Test change_process_automatically
        """
        sickbeard.autoPostProcessorScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickbeard.PROCESS_AUTOMATICALLY = True

        config.change_process_automatically(True) # no change
        self.assertTrue(sickbeard.PROCESS_AUTOMATICALLY)
        config.change_process_automatically('stop') # = defaults to False
        self.assertFalse(sickbeard.PROCESS_AUTOMATICALLY and sickbeard.autoPostProcessorScheduler.enable)
        config.change_process_automatically('on')
        self.assertTrue(sickbeard.PROCESS_AUTOMATICALLY and sickbeard.autoPostProcessorScheduler.enable)


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
