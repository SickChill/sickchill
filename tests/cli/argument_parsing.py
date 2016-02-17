import os
import sys
import unittest

TESTS_DIR = os.path.abspath(__file__)[:-len(os.path.basename(__file__))]
sys.path.insert(1, os.path.join(TESTS_DIR, '../lib'))
sys.path.insert(1, os.path.join(TESTS_DIR, '..'))

import SickBeard
import sickbeard


class TestArgumentParsing(unittest.TestCase):
    def test_quiet(self):
        """
        -q, --quiet: disables logging to console
        """
        s = SickBeard.SickRage()
        sys.argv = ['sick', '-q']
        s.setup_from_command_line()
        assert s.console_logging is False

        s = SickBeard.SickRage()
        sys.argv = ['sick', '--quiet']
        s.setup_from_command_line()
        assert s.console_logging is False

    def test_nolaunch(self):
        """
        --nolaunch: suppress launching web browser on startup
        """
        s = SickBeard.SickRage()
        sys.argv = ['sick', '--nolaunch']
        s.setup_from_command_line()
        assert s.no_launch is True

    @unittest.skipUnless('linux' in sys.platform, 'Linux only test')
    def test_daemon_linux(self):
        """
        -d, --daemon: run as daemon (includes options --quiet --nolaunch)
        """
        s = SickBeard.SickRage()
        sys.argv = ['sick', '--daemon']
        s.setup_from_command_line()
        assert s.run_as_daemon is True
        assert s.console_logging is False
        assert s.no_launch is True

    @unittest.skipUnless('win' in sys.platform or 'darwin' in sys.platform,
                         'Mac/Windows only test')
    def test_daemon_mac_or_windows(self):
        """
        -d, --daemon: run as daemon (includes options --quiet --nolaunch)
        """
        s = SickBeard.SickRage()
        sys.argv = ['sick', '--daemon']
        s.setup_from_command_line()
        assert s.run_as_daemon is False
        assert s.console_logging is False
        assert s.no_launch is True

    def test_pidfile(self):
        """
        --pidfile PIDFILE: combined with --daemon creates a pidfile (full path)
        """
        s = SickBeard.SickRage()
        pid_file = '/tmp/file.pid'
        sys.argv = ['sick', '--daemon', '--pidfile', pid_file]
        s.setup_from_command_line()
        assert s.pid_file == pid_file

    def test_port(self):
        """
        -p PORT, --port PORT: port to listen on
        """
        s = SickBeard.SickRage()
        port = 42
        sys.argv = ['sick', '-p', str(port)]
        s.setup_from_command_line()
        assert s.forced_port == port

        s = SickBeard.SickRage()
        port = 42
        sys.argv = ['sick', '--port', str(port)]
        s.setup_from_command_line()
        assert s.forced_port == port

    def test_datadir(self):
        """
        --datadir DATADIR: folder full path to store database, configfile, cache
        and logfiles
        """
        s = SickBeard.SickRage()
        data_dir = '/tmp'
        sys.argv = ['sick', '--datadir', data_dir]
        s.setup_from_command_line()
        assert sickbeard.DATA_DIR == data_dir

    def test_config(self):
        """
        --config CONFIG: config file full path to load configuration from
        """
        s = SickBeard.SickRage()
        cfg_file = '/tmp/file.cfg'
        sys.argv = ['sick', '--config', cfg_file]
        s.setup_from_command_line()
        assert sickbeard.CONFIG_FILE == cfg_file

    def test_no_resize(self):
        """
        --noresize: prevent resizing of the banner/posters even if PIL is
        installed
        """
        s = SickBeard.SickRage()
        sys.argv = ['sick', '--noresize']
        s.setup_from_command_line()
        assert sickbeard.NO_RESIZE is True
