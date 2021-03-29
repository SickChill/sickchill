import logging
import os.path
import sys
import unittest
from collections import namedtuple

from configobj import ConfigObj

from sickchill import settings
from sickchill.oldbeard import config, scheduler


class ConfigTestBasic(unittest.TestCase):
    """
    Test basic methods in oldbeard.config
    """

    def test_check_section(self):
        """
        Test check_section
        """
        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        assert not config.check_section(CFG, "General")
        assert config.check_section(CFG, "General")

    def test_checkbox_to_value(self):
        """
        Test checkbox_to_value
        """
        assert config.checkbox_to_value(1)
        assert config.checkbox_to_value(["option", "True"])
        assert config.checkbox_to_value("0", "yes", "no") == "no"

    def test_clean_host(self):
        """
        Test clean_host
        """
        assert config.clean_host("http://127.0.0.1:8080") == "127.0.0.1:8080"
        assert config.clean_host("https://mail.google.com/mail") == "mail.google.com"
        assert config.clean_host("http://localhost:8081/home/displayShow?show=80379#season-10") == "localhost:8081"
        assert config.clean_host("http://testme.co.uk", 9000) == "testme.co.uk:9000"  # default port
        assert config.clean_host("www.google.com/search") == "www.google.com"
        assert config.clean_host("") == ""  # empty host

    def test_clean_hosts(self):
        """
        Test clean_hosts
        """
        dirty_hosts = (
            "http://127.0.0.1:8080,https://mail.google.com/mail," "http://localhost:8081/home/displayShow?show=80379#season-10," "www.google.com/search,"
        )
        clean_result = "127.0.0.1:8080,mail.google.com:5050,localhost:8081,www.google.com:5050"
        assert config.clean_hosts(dirty_hosts, "5050") == clean_result

    def test_clean_url(self):
        """
        Test cleaning of urls
        """
        log = logging.getLogger(__name__)
        test = namedtuple("test", "expected_result dirty clean")

        url_tests = [
            test(True, "https://subdomain.domain.tld/endpoint", "https://subdomain.domain.tld/endpoint"),  # does not add a final /
            test(True, "http://www.example.com/folder/", "http://www.example.com/folder/"),  # does not remove the final /
            test(True, "google.com/xml.rpc", "http://google.com/xml.rpc"),  # add scheme if missing
            test(True, "google.com", "http://google.com/"),  # add scheme if missing and final / if its just the domain
            test(True, "scgi:///home/user/.config/path/socket", "scgi:///home/user/.config/path/socket"),  # scgi identified as scheme
            test(True, None, ""),  # None URL returns empty string
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
                    assert config.clean_url(test_url.dirty) == test_url.clean
            elif test_url.expected_result is True:
                assert config.clean_url(test_url.dirty) == test_url.clean
            elif test_url.expected_result is False:
                assert config.clean_url(test_url.dirty) != test_url.clean
            else:
                log.error("Test not defined for %s", test_url)

    def test_min_max(self):
        """
        Test min_max
        """

        assert config.min_max("100", default=50, low=50, high=200) == 100
        assert config.min_max("25", default=50, low=50, high=200) == 50
        assert config.min_max("250", default=50, low=50, high=200) == 200

    def test_check_setting_int(self):
        """
        Test check_setting_int
        """
        # setup
        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        config.check_section(CFG, "General")
        CFG["General"]["indexer_timeout"] = 60
        CFG["General"]["use_icacls"] = "True"
        CFG["General"]["use_nzbs"] = "False"
        CFG["General"]["status_default"] = None
        # normal
        assert config.check_setting_int(CFG, "General", "indexer_timeout", 30) == 60
        assert CFG["General"]["indexer_timeout"] == 60
        # force min/max
        assert config.check_setting_int(CFG, "General", "indexer_timeout", 150, 100, 200) == 150
        assert CFG["General"]["indexer_timeout"] == 150
        assert config.check_setting_int(CFG, "General", "indexer_timeout", 250, 200, 300, False) == 200
        assert CFG["General"]["indexer_timeout"] == 200
        assert config.check_setting_int(CFG, "General", "indexer_timeout", 90, 50, 100) == 90
        assert CFG["General"]["indexer_timeout"] == 90
        assert config.check_setting_int(CFG, "General", "indexer_timeout", 20, 10, 30, False) == 30
        assert CFG["General"]["indexer_timeout"] == 30
        # true/false => int
        assert config.check_setting_int(CFG, "General", "use_icacls", 1) == 1
        assert CFG["General"]["use_icacls"] == "True"
        assert config.check_setting_int(CFG == "General", "use_nzbs", 0), 0
        assert CFG["General"]["use_nzbs"] == "False"
        # None value type + silent off
        assert config.check_setting_int(CFG == "General", "status_default", 5, silent=False), 5
        assert CFG["General"]["status_default"] == 5
        # unmatched section
        assert config.check_setting_int(CFG == "Subtitles", "subtitles_finder_frequency", 1), 1
        assert CFG["Subtitles"]["subtitles_finder_frequency"] == 1
        # wrong def_val/min/max type
        assert config.check_setting_int(CFG == "General", "indexer_timeout", "ba", "min", "max"), 30
        assert CFG["General"]["indexer_timeout"] == 30

    def test_check_setting_float(self):
        """
        Test check_setting_float
        """
        # setup
        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        config.check_section(CFG, "General")
        CFG["General"]["fanart_background_opacity"] = 0.5
        CFG["General"]["log_size"] = None
        # normal
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", 0.4), 0.5
        assert CFG["General"]["fanart_background_opacity"] == 0.5
        # force min/max
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", 0.7, 0.6, 1.0), 0.7
        assert CFG["General"]["fanart_background_opacity"] == 0.7
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", 0.7, 0.8, 1.0, False), 0.8
        assert CFG["General"]["fanart_background_opacity"] == 0.8
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", 0.3, 0.1, 0.4), 0.3
        assert CFG["General"]["fanart_background_opacity"] == 0.3
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", 0.1, 0.1, 0.2, False), 0.2
        assert CFG["General"]["fanart_background_opacity"] == 0.2
        # None value type + silent off
        assert config.check_setting_float(CFG == "General", "log_size", 10.0, silent=False), 10.0
        assert CFG["General"]["log_size"] == 10.0
        # unmatched section
        assert config.check_setting_float(CFG == "Kodi", "log_size", 2.5), 2.5
        assert CFG["Kodi"]["log_size"] == 2.5
        # wrong def_val/min/max type
        assert config.check_setting_float(CFG == "General", "fanart_background_opacity", "ba", "min", "max"), 0.2
        assert CFG["General"]["fanart_background_opacity"] == 0.2

    def test_check_setting_str(self):
        """
        Test check_setting_str
        """
        # setup
        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        config.check_section(CFG, "General")
        CFG["General"]["process_method"] = "copy"
        CFG["General"]["git_password"] = "SFa342FHb_"  # noqa: S105
        CFG["General"]["extra_scripts"] = None
        # normal
        assert config.check_setting_str(CFG == "General", "process_method", "move"), "copy"
        assert config.check_setting_str(CFG == "General", "git_password", "", silent=False, censor_log=True), "SFa342FHb_"
        # None value type
        assert config.check_setting_str(CFG == "General", "extra_scripts", ""), ""
        # unmatched section
        assert config.check_setting_str(CFG == "Subtitles", "subtitles_languages", "eng"), "eng"
        # wrong def_val type
        assert config.check_setting_str(CFG == "General", "process_method", ["fail"]), "copy"

    def test_check_setting_bool(self):
        """
        Test check_setting_bool
        """
        # setup
        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        config.check_section(CFG, "General")
        CFG["General"]["debug"] = True
        CFG["General"]["season_folders_default"] = False
        CFG["General"]["dbdebug"] = None
        # normal
        assert config.check_setting_bool(CFG, "General", "debug")
        assert not config.check_setting_bool(CFG, "General", "season_folders_default", def_val=True)
        # None value type
        assert not config.check_setting_bool(CFG, "General", "dbdebug", False)
        # unmatched item
        assert config.check_setting_bool(CFG, "General", "git_reset", def_val=True)
        # unmatched section
        assert not config.check_setting_bool(CFG, "Subtitles", "use_subtitles", def_val=False)
        # wrong def_val type, silent = off
        assert config.check_setting_bool(CFG, "General", "debug", def_val=["fail"], silent=False)


class ConfigTestChanges(unittest.TestCase):
    """
    Test change methods in oldbeard.config
    """

    def test_change_https_cert(self):
        """
        Test change_https_cert
        """
        settings.HTTPS_CERT = "server.crt"  # Initialize
        assert config.change_https_cert("")
        assert config.change_https_cert("server.crt")
        assert not config.change_https_cert("/:/server.crt")  # INVALID
        settings.HTTPS_CERT = ""

    def test_change_https_key(self):
        """
        Test change_https_key
        """
        settings.HTTPS_KEY = "server.key"  # Initialize
        assert config.change_https_key("")
        assert config.change_https_key("server.key")
        assert not config.change_https_key("/:/server.key")  # INVALID
        settings.HTTPS_KEY = ""

    def test_change_sickchill_background(self):
        """
        Test change_sickchill_background
        """
        settings.SICKCHILL_BACKGROUND_PATH = ""  # Initialize
        assert config.change_sickchill_background(__file__)
        assert not config.change_sickchill_background("not_real.jpg")
        assert config.change_sickchill_background("")

    def test_change_custom_css(self):
        """
        Test change_custom_css
        """
        settings.CUSTOM_CSS_PATH = ""  # Initialize
        assert not config.change_custom_css(__file__)  # not a css file
        assert not config.change_custom_css("not_real.jpg")  # doesn't exist
        assert not config.change_custom_css("sickchill_tests")  # isn't a file
        css_file = os.path.join(os.path.dirname(__file__), "custom.css")
        with open(css_file, "w") as f:
            f.write("table.main {\n    width: 100%;\n}")
        assert config.change_custom_css(css_file)  # real
        os.remove(css_file)
        assert config.change_custom_css("")  # empty

    def test_change_nzb_dir(self):
        """
        Test change_nzb_dir
        """
        settings.NZB_DIR = ""
        assert config.change_nzb_dir("cache")
        assert not config.change_nzb_dir("/:/NZB_Downloads")  # INVALID
        assert config.change_nzb_dir("")

    def test_change_torrent_dir(self):
        """
        Test change_torrent_dir
        """
        settings.TORRENT_DIR = ""
        assert config.change_torrent_dir("cache")
        assert not config.change_torrent_dir("/:/Downloads")  # INVALID
        assert config.change_torrent_dir("")

    def test_change_tv_download_dir(self):
        """
        Test change_tv_download_dir
        """
        settings.TV_DOWNLOAD_DIR = ""
        assert config.change_tv_download_dir("cache")
        assert not config.change_tv_download_dir("/:/Downloads/Completed")  # INVALID

        assert config.change_tv_download_dir("")
        assert settings.TV_DOWNLOAD_DIR == ""

    def test_change_unpack_dir(self):
        """
        Test change_unpack_dir
        """
        settings.UNPACK_DIR = ""
        assert config.change_unpack_dir("cache")
        assert not config.change_unpack_dir("/:/Extract")  # INVALID
        assert config.change_unpack_dir("")

    def test_change_auto_pp_freq(self):
        """
        Test change_postprocessor_frequency
        """
        settings.autoPostProcessorScheduler = scheduler.Scheduler(lambda: None)  # dummy

        config.change_postprocessor_frequency(0)
        assert settings.AUTOPOSTPROCESSOR_FREQUENCY == settings.MIN_AUTOPOSTPROCESSOR_FREQUENCY
        config.change_postprocessor_frequency("s")
        assert settings.AUTOPOSTPROCESSOR_FREQUENCY == settings.DEFAULT_AUTOPOSTPROCESSOR_FREQUENCY
        config.change_postprocessor_frequency(60)
        assert settings.AUTOPOSTPROCESSOR_FREQUENCY == 60

    def test_change_daily_search_freq(self):
        """
        Test change_daily_search_frequency
        """
        settings.dailySearchScheduler = scheduler.Scheduler(lambda: None)  # dummy

        config.change_daily_search_frequency(0)
        assert settings.DAILYSEARCH_FREQUENCY == settings.MIN_DAILYSEARCH_FREQUENCY
        config.change_daily_search_frequency("s")
        assert settings.DAILYSEARCH_FREQUENCY == settings.DEFAULT_DAILYSEARCH_FREQUENCY
        config.change_daily_search_frequency(60)
        assert settings.DAILYSEARCH_FREQUENCY == 60

    def test_change_backlog_freq(self):
        """
        Test change_backlog_frequency
        """
        settings.backlogSearchScheduler = scheduler.Scheduler(lambda: None)  # dummy
        settings.DAILYSEARCH_FREQUENCY = settings.DEFAULT_DAILYSEARCH_FREQUENCY  # needed

        config.change_backlog_frequency(0)
        assert settings.BACKLOG_FREQUENCY == settings.MIN_BACKLOG_FREQUENCY
        config.change_backlog_frequency("s")
        assert settings.BACKLOG_FREQUENCY == settings.MIN_BACKLOG_FREQUENCY
        config.change_backlog_frequency(1440)
        assert settings.BACKLOG_FREQUENCY == 1440

    def test_change_update_freq(self):
        """
        Test change_update_frequency
        """
        settings.versionCheckScheduler = scheduler.Scheduler(lambda: None)  # dummy

        config.change_update_frequency(0)
        assert settings.UPDATE_FREQUENCY == settings.MIN_UPDATE_FREQUENCY
        config.change_update_frequency("s")
        assert settings.UPDATE_FREQUENCY == settings.DEFAULT_UPDATE_FREQUENCY
        config.change_update_frequency(60)
        assert settings.UPDATE_FREQUENCY == 60

    def test_change_show_update_hour(self):
        """
        Test change_showupdate_hour
        """
        settings.showUpdateScheduler = scheduler.Scheduler(lambda: None)  # dummy

        config.change_showupdate_hour(-2)
        assert settings.SHOWUPDATE_HOUR == 0
        config.change_showupdate_hour("s")
        assert settings.SHOWUPDATE_HOUR == settings.DEFAULT_SHOWUPDATE_HOUR
        config.change_showupdate_hour(60)
        assert settings.SHOWUPDATE_HOUR == 0
        config.change_showupdate_hour(12)
        assert settings.SHOWUPDATE_HOUR == 12

    def test_change_sub_finder_freq(self):
        """
        Test change_subtitle_finder_frequency
        """
        config.change_subtitle_finder_frequency("")
        assert settings.SUBTITLES_FINDER_FREQUENCY == 1
        config.change_subtitle_finder_frequency("s")
        assert settings.SUBTITLES_FINDER_FREQUENCY == 1
        config.change_subtitle_finder_frequency(8)
        assert settings.SUBTITLES_FINDER_FREQUENCY == 8

    def test_change_version_notify(self):
        """
        Test change_version_notify
        """

        class dummy_action(object):  # needed for *scheduler.action.forceRun()
            def __init__(self):
                self.amActive = False

        settings.versionCheckScheduler = scheduler.Scheduler(dummy_action())  # dummy
        settings.VERSION_NOTIFY = True

        config.change_version_notify(True)  # no change
        assert settings.VERSION_NOTIFY
        config.change_version_notify("stop")  # = defaults to False
        assert not settings.VERSION_NOTIFY
        assert not settings.versionCheckScheduler.enable
        config.change_version_notify("on")
        assert settings.VERSION_NOTIFY
        assert settings.versionCheckScheduler.enable

    def test_change_download_propers(self):
        """
        Test change_download_propers
        """
        settings.properFinderScheduler = scheduler.Scheduler(lambda: None)  # dummy
        settings.DOWNLOAD_PROPERS = True

        config.change_download_propers(True)  # no change
        assert settings.DOWNLOAD_PROPERS
        config.change_download_propers("stop")  # = defaults to False
        assert not settings.DOWNLOAD_PROPERS
        assert not settings.properFinderScheduler.enable
        config.change_download_propers("on")
        assert settings.DOWNLOAD_PROPERS
        assert settings.properFinderScheduler.enable

    def test_change_use_trakt(self):
        """
        Test change_use_trakt
        """
        settings.traktCheckerScheduler = scheduler.Scheduler(lambda: None)  # dummy
        settings.USE_TRAKT = True

        config.change_use_trakt(True)  # no change
        assert settings.USE_TRAKT
        config.change_use_trakt("stop")  # = defaults to False
        assert not settings.USE_TRAKT
        assert not settings.traktCheckerScheduler.enable
        config.change_use_trakt("on")
        assert settings.USE_TRAKT
        assert settings.traktCheckerScheduler.enable

    def test_change_use_subtitles(self):
        """
        Test change_use_subtitles
        """
        settings.subtitlesFinderScheduler = scheduler.Scheduler(lambda: None)  # dummy
        settings.USE_SUBTITLES = True

        config.change_use_subtitles(True)  # no change
        assert settings.USE_SUBTITLES
        config.change_use_subtitles("stop")  # = defaults to False
        assert not settings.USE_SUBTITLES
        assert not settings.subtitlesFinderScheduler.enable
        config.change_use_subtitles("on")
        assert settings.USE_SUBTITLES
        assert settings.subtitlesFinderScheduler.enable

    def test_change_process_auto(self):
        """
        Test change_process_automatically
        """
        settings.autoPostProcessorScheduler = scheduler.Scheduler(lambda: None)  # dummy
        settings.PROCESS_AUTOMATICALLY = True

        config.change_process_automatically(True)  # no change
        assert settings.PROCESS_AUTOMATICALLY
        config.change_process_automatically("stop")  # = defaults to False
        assert not settings.PROCESS_AUTOMATICALLY
        assert not settings.autoPostProcessorScheduler.enable
        config.change_process_automatically("on")
        assert settings.PROCESS_AUTOMATICALLY
        assert settings.autoPostProcessorScheduler.enable


class ConfigTestMigrator(unittest.TestCase):
    """
    Test the oldbeard.config.ConfigMigrator class
    """

    @unittest.expectedFailure  # Not fully implemented
    def test_config_migrator(self):
        """
        Test migrate_config
        """
        # TODO: Assert the 'too-advanced-config-version' error

        CFG = ConfigObj("config.ini", encoding="UTF-8", indent_type="  ")
        config.check_section(CFG, "General")
        CFG["General"]["config_version"] = 0
        settings.CONFIG_VERSION = 13
        settings.CONFIG_FILE = "config.ini"

        migrator = config.ConfigMigrator(CFG)
        migrator.migrate_config()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger(__name__).setLevel(logging.DEBUG)

    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestBasic)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestChanges)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
    SUITE = unittest.TestLoader().loadTestsFromTestCase(ConfigTestMigrator)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
