# coding=utf-8
"""
Test sickchill.config's classes and methods

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
        _migrate_v8
        _migrate_v9
        _migrate_v10

Methods
    change_https_cert
    change_https_key
    change_unrar_tool
    change_sickchill_background
    change_custom_css
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
    check_section
    checkbox_to_value
    clean_host
    clean_hosts
    clean_url
    min_max
    check_setting_int
    check_setting_float
    check_setting_str
    check_setting_bool
"""

# pylint: disable=line-too-long
from __future__ import absolute_import, unicode_literals

import logging
import os.path
import platform
import sys
import unittest
import mock
from collections import namedtuple

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '../lib')))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sickchill import config, scheduler
from configobj import ConfigObj
from rarfile import RarExecError
import sickchill


class ConfigTestBasic(unittest.TestCase):
    """
    Test basic methods in sickchill.config
    """

    def test_check_section(self):
        """
        Test check_section
        """
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        self.assertFalse(config.check_section(CFG, 'General'))
        self.assertTrue(config.check_section(CFG, 'General'))

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

    def test_min_max(self):
        """
        Test min_max
        """

        self.assertEqual(config.min_max('100', default=50, low=50, high=200), 100)
        self.assertEqual(config.min_max('25', default=50, low=50, high=200), 50)
        self.assertEqual(config.min_max('250', default=50, low=50, high=200), 200)

    def test_check_setting_int(self):
        """
        Test check_setting_int
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.check_section(CFG, 'General')
        CFG['General']['indexer_timeout'] = 60
        CFG['General']['use_icacls'] = 'True'
        CFG['General']['use_nzbs'] = 'False'
        CFG['General']['status_default'] = None
        # normal
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 30), 60)
        self.assertEqual(CFG['General']['indexer_timeout'], 60)
        # force min/max
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 150, 100, 200), 150)
        self.assertEqual(CFG['General']['indexer_timeout'], 150)
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 250, 200, 300, False), 200)
        self.assertEqual(CFG['General']['indexer_timeout'], 200)
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 90, 50, 100), 90)
        self.assertEqual(CFG['General']['indexer_timeout'], 90)
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 20, 10, 30, False), 30)
        self.assertEqual(CFG['General']['indexer_timeout'], 30)
        # true/false => int
        self.assertEqual(config.check_setting_int(CFG, 'General', 'use_icacls', 1), 1)
        self.assertEqual(CFG['General']['use_icacls'], 'True')
        self.assertEqual(config.check_setting_int(CFG, 'General', 'use_nzbs', 0), 0)
        self.assertEqual(CFG['General']['use_nzbs'], 'False')
        # None value type + silent off
        self.assertEqual(config.check_setting_int(CFG, 'General', 'status_default', 5, silent=False), 5)
        self.assertEqual(CFG['General']['status_default'], 5)
        # unmatched section
        self.assertEqual(config.check_setting_int(CFG, 'Subtitles', 'subtitles_finder_frequency', 1), 1)
        self.assertEqual(CFG['Subtitles']['subtitles_finder_frequency'], 1)
        # wrong def_val/min/max type
        self.assertEqual(config.check_setting_int(CFG, 'General', 'indexer_timeout', 'ba', 'min', 'max'), 30)
        self.assertEqual(CFG['General']['indexer_timeout'], 30)

    def test_check_setting_float(self):
        """
        Test check_setting_float
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.check_section(CFG, 'General')
        CFG['General']['fanart_background_opacity'] = 0.5
        CFG['General']['log_size'] = None
        # normal
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.4), 0.5)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.5)
        # force min/max
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.7, 0.6, 1.0), 0.7)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.7)
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.7, 0.8, 1.0, False), 0.8)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.8)
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.3, 0.1, 0.4), 0.3)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.3)
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 0.1, 0.1, 0.2, False), 0.2)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.2)
        # None value type + silent off
        self.assertEqual(config.check_setting_float(CFG, 'General', 'log_size', 10.0, silent=False), 10.0)
        self.assertEqual(CFG['General']['log_size'], 10.0)
        # unmatched section
        self.assertEqual(config.check_setting_float(CFG, 'Kodi', 'log_size', 2.5), 2.5)
        self.assertEqual(CFG['Kodi']['log_size'], 2.5)
        # wrong def_val/min/max type
        self.assertEqual(config.check_setting_float(CFG, 'General', 'fanart_background_opacity', 'ba', 'min', 'max'), 0.2)
        self.assertEqual(CFG['General']['fanart_background_opacity'], 0.2)

    def test_check_setting_str(self):
        """
        Test check_setting_str
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.check_section(CFG, 'General')
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
        # wrong def_val type
        self.assertEqual(config.check_setting_str(CFG, 'General', 'process_method', ['fail']), 'copy')

    def test_check_setting_bool(self):
        """
        Test check_setting_bool
        """
        # setup
        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.check_section(CFG, 'General')
        CFG['General']['debug'] = True
        CFG['General']['season_folders_default'] = False
        CFG['General']['dbdebug'] = None
        # normal
        self.assertTrue(config.check_setting_bool(CFG, 'General', 'debug'))
        self.assertFalse(config.check_setting_bool(CFG, 'General', 'season_folders_default', def_val=True))
        # None value type
        self.assertFalse(config.check_setting_bool(
            CFG, 'General', 'dbdebug', False))
        # unmatched item
        self.assertTrue(config.check_setting_bool(CFG, 'General', 'git_reset', def_val=True))
        # unmatched section
        self.assertFalse(config.check_setting_bool(CFG, 'Subtitles', 'use_subtitles', def_val=False))
        # wrong def_val type, silent = off
        self.assertTrue(config.check_setting_bool(
            CFG, 'General', 'debug', def_val=['fail'], silent=False))


class ConfigTestChanges(unittest.TestCase):
    """
    Test change methods in sickchill.config
    """

    def test_change_https_cert(self):
        """
        Test change_https_cert
        """
        sickchill.HTTPS_CERT = 'server.crt' # Initialize
        self.assertTrue(config.change_https_cert(''))
        self.assertTrue(config.change_https_cert('server.crt'))
        self.assertFalse(config.change_https_cert('/:/server.crt')) # INVALID
        sickchill.HTTPS_CERT = ''

    def test_change_https_key(self):
        """
        Test change_https_key
        """
        sickchill.HTTPS_KEY = 'server.key'  # Initialize
        self.assertTrue(config.change_https_key(''))
        self.assertTrue(config.change_https_key('server.key'))
        self.assertFalse(config.change_https_key('/:/server.key')) # INVALID
        sickchill.HTTPS_KEY = ''

    # def test_change_unrar_tool(self):
    #     """
    #     Test change_unrar_tool
    #     """
    #     sickchill.PROG_DIR = ''
    #     custom_check_mock = mock.patch('rarfile.custom_check', mock.MagicMock())
    #
    #     if platform.system() != 'Windows':
    #         custom_check_mock.new.side_effect = [RarExecError(), RarExecError(), RarExecError(), RarExecError(), True]
    #         with custom_check_mock:
    #             self.assertTrue(config.change_unrar_tool('UNKNOWN', 'UNKNOWN'))
    #
    #         # Test when none are installed, even defaults, that we return false
    #         custom_check_mock.new.side_effect = RarExecError()
    #         with custom_check_mock:
    #             self.assertFalse(config.change_unrar_tool('unrar', 'bsdtar'))
    #
    #     else:
    #         # Test removing bad unrar
    #         custom_check_mock.new.side_effect = [True, True]
    #         with custom_check_mock, \
    #              mock.patch('os.path.exists', mock.MagicMock(return_value=True)), \
    #              mock.patch('os.path.getsize', mock.MagicMock(return_value=447440)), \
    #              mock.patch('os.remove'):
    #             self.assertTrue(config.change_unrar_tool('unrar', 'bsdtar'))
    #
    #         my_environ = mock.patch.dict(os.environ,
    #                                      {'ProgramFiles': 'C:\\Program Files (x86)\\',
    #                                       'ProgramFiles(x86)': 'C:\\Program Files (x86)\\',
    #                                       'ProgramW6432': 'C:\\Program Files\\'}, clear=True)
    #         with custom_check_mock, my_environ, mock.patch('rarfile.ORIG_UNRAR_TOOL', 'UNKNOWN'), mock.patch('rarfile.UNRAR_TOOL', 'UNKNOWN'), \
    #              mock.patch('rarfile.ALT_TOOL', 'UNKNOWN'), mock.patch('sickchill.UNRAR_TOOL', 'UNKNOWN'), mock.patch('sickchill.ALT_UNRAR_TOOL', 'UNKNOWN'):
    #             # Test that on windows it downloads unrar for them.
    #             self.assertTrue(config.change_unrar_tool('NOPE', 'NOWAY'))

    def test_change_sickchill_background(self):
        """
        Test change_sickchill_background
        """
        sickchill.SICKCHILL_BACKGROUND_PATH = ''  # Initialize
        self.assertTrue(config.change_sickchill_background(__file__))
        self.assertFalse(config.change_sickchill_background('not_real.jpg'))
        self.assertTrue(config.change_sickchill_background(''))

    def test_change_custom_css(self):
        """
        Test change_custom_css
        """
        sickchill.CUSTOM_CSS_PATH = ''  # Initialize
        self.assertFalse(config.change_custom_css(__file__)) # not a css file
        self.assertFalse(config.change_custom_css('not_real.jpg')) # doesn't exist
        self.assertFalse(config.change_custom_css('sickchill_tests')) # isn't a file
        css_file = os.path.join(os.path.dirname(__file__), 'custom.css')
        with open(css_file, 'w') as f:
            f.write('table.main {\n    width: 100%;\n}')
        self.assertTrue(config.change_custom_css(css_file)) # real
        os.remove(css_file)
        self.assertTrue(config.change_custom_css('')) # empty

    def test_change_log_dir(self):
        """
        Test change_log_dir
        """
        sickchill.DATA_DIR = os.path.dirname(__file__)
        sickchill.ACTUAL_LOG_DIR = ''
        sickchill.LOG_DIR = os.path.join(sickchill.DATA_DIR, sickchill.ACTUAL_LOG_DIR)
        sickchill.WEB_LOG = False

        self.assertFalse(config.change_log_dir('/:/Logs', True))
        self.assertTrue(config.change_log_dir('Logs', True))

    def test_change_nzb_dir(self):
        """
        Test change_nzb_dir
        """
        sickchill.NZB_DIR = ''
        self.assertTrue(config.change_nzb_dir('cache'))
        self.assertFalse(config.change_nzb_dir('/:/NZB_Downloads')) # INVALID
        self.assertTrue(config.change_nzb_dir(''))

    def test_change_torrent_dir(self):
        """
        Test change_torrent_dir
        """
        sickchill.TORRENT_DIR = ''
        self.assertTrue(config.change_torrent_dir('cache'))
        self.assertFalse(config.change_torrent_dir('/:/Downloads')) # INVALID
        self.assertTrue(config.change_torrent_dir(''))

    def test_change_tv_download_dir(self):
        """
        Test change_tv_download_dir
        """
        sickchill.TV_DOWNLOAD_DIR = ''
        self.assertTrue(config.change_tv_download_dir('cache'))
        self.assertFalse(config.change_tv_download_dir('/:/Downloads/Completed')) # INVALID

        self.assertTrue(config.change_tv_download_dir(''))
        self.assertEqual(sickchill.TV_DOWNLOAD_DIR, '')

    def test_change_unpack_dir(self):
        """
        Test change_unpack_dir
        """
        sickchill.UNPACK_DIR = ''
        self.assertTrue(config.change_unpack_dir('cache'))
        self.assertFalse(config.change_unpack_dir('/:/Extract')) # INVALID
        self.assertTrue(config.change_unpack_dir(''))

    def test_change_auto_pp_freq(self):
        """
        Test change_postprocessor_frequency
        """
        sickchill.autoPostProcessorScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_postprocessor_frequency(0)
        self.assertEqual(sickchill.AUTOPOSTPROCESSOR_FREQUENCY, sickchill.MIN_AUTOPOSTPROCESSOR_FREQUENCY)
        config.change_postprocessor_frequency('s')
        self.assertEqual(sickchill.AUTOPOSTPROCESSOR_FREQUENCY, sickchill.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY)
        config.change_postprocessor_frequency(60)
        self.assertEqual(sickchill.AUTOPOSTPROCESSOR_FREQUENCY, 60)

    def test_change_daily_search_freq(self):
        """
        Test change_daily_search_frequency
        """
        sickchill.dailySearchScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_daily_search_frequency(0)
        self.assertEqual(sickchill.DAILYSEARCH_FREQUENCY, sickchill.MIN_DAILYSEARCH_FREQUENCY)
        config.change_daily_search_frequency('s')
        self.assertEqual(sickchill.DAILYSEARCH_FREQUENCY, sickchill.DEFAULT_DAILYSEARCH_FREQUENCY)
        config.change_daily_search_frequency(60)
        self.assertEqual(sickchill.DAILYSEARCH_FREQUENCY, 60)

    def test_change_backlog_freq(self):
        """
        Test change_backlog_frequency
        """
        sickchill.backlogSearchScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickchill.DAILYSEARCH_FREQUENCY = sickchill.DEFAULT_DAILYSEARCH_FREQUENCY # needed

        config.change_backlog_frequency(0)
        self.assertEqual(sickchill.BACKLOG_FREQUENCY, sickchill.MIN_BACKLOG_FREQUENCY)
        config.change_backlog_frequency('s')
        self.assertEqual(sickchill.BACKLOG_FREQUENCY, sickchill.MIN_BACKLOG_FREQUENCY)
        config.change_backlog_frequency(1440)
        self.assertEqual(sickchill.BACKLOG_FREQUENCY, 1440)

    def test_change_update_freq(self):
        """
        Test change_update_frequency
        """
        sickchill.versionCheckScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_update_frequency(0)
        self.assertEqual(sickchill.UPDATE_FREQUENCY, sickchill.MIN_UPDATE_FREQUENCY)
        config.change_update_frequency('s')
        self.assertEqual(sickchill.UPDATE_FREQUENCY, sickchill.DEFAULT_UPDATE_FREQUENCY)
        config.change_update_frequency(60)
        self.assertEqual(sickchill.UPDATE_FREQUENCY, 60)

    def test_change_show_update_hour(self):
        """
        Test change_showupdate_hour
        """
        sickchill.showUpdateScheduler = scheduler.Scheduler(lambda:None) # dummy

        config.change_showupdate_hour(-2)
        self.assertEqual(sickchill.SHOWUPDATE_HOUR, 0)
        config.change_showupdate_hour('s')
        self.assertEqual(sickchill.SHOWUPDATE_HOUR, sickchill.DEFAULT_SHOWUPDATE_HOUR)
        config.change_showupdate_hour(60)
        self.assertEqual(sickchill.SHOWUPDATE_HOUR, 0)
        config.change_showupdate_hour(12)
        self.assertEqual(sickchill.SHOWUPDATE_HOUR, 12)

    def test_change_sub_finder_freq(self):
        """
        Test change_subtitle_finder_frequency
        """
        config.change_subtitle_finder_frequency('')
        self.assertEqual(sickchill.SUBTITLES_FINDER_FREQUENCY, 1)
        config.change_subtitle_finder_frequency('s')
        self.assertEqual(sickchill.SUBTITLES_FINDER_FREQUENCY, 1)
        config.change_subtitle_finder_frequency(8)
        self.assertEqual(sickchill.SUBTITLES_FINDER_FREQUENCY, 8)

    def test_change_version_notify(self):
        """
        Test change_version_notify
        """
        class dummy_action(object): # needed for *scheduler.action.forceRun()
            def __init__(self):
                self.amActive = False

        sickchill.versionCheckScheduler = scheduler.Scheduler(dummy_action()) # dummy
        sickchill.VERSION_NOTIFY = True

        config.change_version_notify(True) # no change
        self.assertTrue(sickchill.VERSION_NOTIFY)
        config.change_version_notify('stop') # = defaults to False
        self.assertFalse(sickchill.VERSION_NOTIFY and sickchill.versionCheckScheduler.enable)
        config.change_version_notify('on')
        self.assertTrue(sickchill.VERSION_NOTIFY and sickchill.versionCheckScheduler.enable)

    def test_change_download_propers(self):
        """
        Test change_download_propers
        """
        sickchill.properFinderScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickchill.DOWNLOAD_PROPERS = True

        config.change_download_propers(True) # no change
        self.assertTrue(sickchill.DOWNLOAD_PROPERS)
        config.change_download_propers('stop') # = defaults to False
        self.assertFalse(sickchill.DOWNLOAD_PROPERS and sickchill.properFinderScheduler.enable)
        config.change_download_propers('on')
        self.assertTrue(sickchill.DOWNLOAD_PROPERS and sickchill.properFinderScheduler.enable)

    def test_change_use_trakt(self):
        """
        Test change_use_trakt
        """
        sickchill.traktCheckerScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickchill.USE_TRAKT = True

        config.change_use_trakt(True) # no change
        self.assertTrue(sickchill.USE_TRAKT)
        config.change_use_trakt('stop') # = defaults to False
        self.assertFalse(sickchill.USE_TRAKT and sickchill.traktCheckerScheduler.enable)
        config.change_use_trakt('on')
        self.assertTrue(sickchill.USE_TRAKT and sickchill.traktCheckerScheduler.enable)

    def test_change_use_subtitles(self):
        """
        Test change_use_subtitles
        """
        sickchill.subtitlesFinderScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickchill.USE_SUBTITLES = True

        config.change_use_subtitles(True) # no change
        self.assertTrue(sickchill.USE_SUBTITLES)
        config.change_use_subtitles('stop') # = defaults to False
        self.assertFalse(sickchill.USE_SUBTITLES and sickchill.subtitlesFinderScheduler.enable)
        config.change_use_subtitles('on')
        self.assertTrue(sickchill.USE_SUBTITLES and sickchill.subtitlesFinderScheduler.enable)

    def test_change_process_auto(self):
        """
        Test change_process_automatically
        """
        sickchill.autoPostProcessorScheduler = scheduler.Scheduler(lambda:None) # dummy
        sickchill.PROCESS_AUTOMATICALLY = True

        config.change_process_automatically(True) # no change
        self.assertTrue(sickchill.PROCESS_AUTOMATICALLY)
        config.change_process_automatically('stop') # = defaults to False
        self.assertFalse(sickchill.PROCESS_AUTOMATICALLY and sickchill.autoPostProcessorScheduler.enable)
        config.change_process_automatically('on')
        self.assertTrue(sickchill.PROCESS_AUTOMATICALLY and sickchill.autoPostProcessorScheduler.enable)


class ConfigTestMigrator(unittest.TestCase):
    """
    Test the sickchill.config.ConfigMigrator class
    """
    @unittest.expectedFailure # Not fully implemented
    def test_config_migrator(self):
        """
        Test migrate_config
        """
        # TODO: Assert the 'too-advanced-config-version' error

        CFG = ConfigObj('config.ini', encoding='UTF-8')
        config.check_section(CFG, 'General')
        CFG['General']['config_version'] = 0
        sickchill.CONFIG_VERSION = 11
        sickchill.CONFIG_FILE = 'config.ini'

        migrator = config.ConfigMigrator(CFG)
        migrator.migrate_config()

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestBasic)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestChanges)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestMigrator)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
