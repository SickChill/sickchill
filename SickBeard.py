#!/usr/bin/env python2.7
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

# Check needed software dependencies to nudge users to fix their setup

# pylint: disable=W0703

from __future__ import with_statement

import codecs

codecs.register(lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

import time
import signal
import sys
import subprocess
import traceback

import os
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))

import shutil
import shutil_custom

shutil.copyfile = shutil_custom.copyfile_custom

if sys.version_info < (2, 7):
    print "Sorry, requires Python 2.7.x"
    sys.exit(1)

if sys.version_info >= (2, 7, 9):
    import ssl
    # pylint: disable=W0212
    ssl._create_default_https_context = ssl._create_unverified_context

import locale
import datetime
import threading
import getopt

import sickbeard
from sickbeard import db, logger, network_timezones, failed_history, name_cache
from sickbeard.tv import TVShow
from sickbeard.webserveInit import SRWebServer
from sickbeard.event_queue import Events
from configobj import ConfigObj
from sickrage.helper.encoding import ek

throwaway = datetime.datetime.strptime('20110101', '%Y%m%d')

signal.signal(signal.SIGINT, sickbeard.sig_handler)
signal.signal(signal.SIGTERM, sickbeard.sig_handler)


class SickRage(object):
    # pylint: disable=R0902
    def __init__(self):
        # system event callback for shutdown/restart
        sickbeard.events = Events(self.shutdown)

        # daemon constants
        self.runAsDaemon = False
        self.CREATEPID = False
        self.PIDFILE = ''

        # webserver constants
        self.webserver = None
        self.forcedPort = None
        self.noLaunch = False

        self.webhost = '0.0.0.0'
        self.startPort = sickbeard.WEB_PORT
        self.web_options = {}

        self.log_dir = None
        self.consoleLogging = True


    @staticmethod
    def help_message():
        """
        print help message for commandline options
        """
        help_msg = "\n"
        help_msg += "Usage: " + sickbeard.MY_FULLNAME + " <option> <another option>\n"
        help_msg += "\n"
        help_msg += "Options:\n"
        help_msg += "\n"
        help_msg += "    -h          --help              Prints this message\n"
        help_msg += "    -q          --quiet             Disables logging to console\n"
        help_msg += "                --nolaunch          Suppress launching web browser on startup\n"

        if sys.platform == 'win32' or sys.platform == 'darwin':
            help_msg += "    -d          --daemon            Running as real daemon is not supported on Windows\n"
            help_msg += "                                    On Windows and MAC, --daemon is substituted with: --quiet --nolaunch\n"
        else:
            help_msg += "    -d          --daemon            Run as double forked daemon (includes options --quiet --nolaunch)\n"
            help_msg += "                --pidfile=<path>    Combined with --daemon creates a pidfile (full path including filename)\n"

        help_msg += "    -p <port>   --port=<port>       Override default/configured port to listen on\n"
        help_msg += "                --datadir=<path>    Override folder (full path) as location for\n"
        help_msg += "                                    storing database, configfile, cache, logfiles \n"
        help_msg += "                                    Default: " + sickbeard.PROG_DIR + "\n"
        help_msg += "                --config=<path>     Override config filename (full path including filename)\n"
        help_msg += "                                    to load configuration from \n"
        help_msg += "                                    Default: config.ini in " + sickbeard.PROG_DIR + " or --datadir location\n"
        help_msg += "                --noresize          Prevent resizing of the banner/posters even if PIL is installed\n"

        return help_msg

    @staticmethod
    def fix_clients_nonsense():

        filenames = [
            "sickbeard/clients/download_station.py",
            "sickbeard/clients/utorrent.py",
            "sickbeard/clients/qbittorrent.py",
            "sickbeard/clients/transmission.py",
            "sickbeard/clients/deluge.py",
            "sickbeard/clients/deluged.py",
            "sickbeard/clients/rtorrent.py"
        ]

        for filename in filenames:
            filename = ek(os.path.join, sickbeard.PROG_DIR, filename)
            try:
                if ek(os.path.exists, filename):
                    ek(os.remove, filename)
            except Exception:
                pass
            try:
                if ek(os.path.exists, filename + "c"):
                    ek(os.remove, filename + "c")
            except Exception:
                pass

    # pylint: disable=R0912,R0915
    def start(self):
        # do some preliminary stuff
        sickbeard.MY_FULLNAME = os.path.normpath(os.path.abspath(__file__))
        sickbeard.MY_NAME = os.path.basename(sickbeard.MY_FULLNAME)
        sickbeard.PROG_DIR = os.path.dirname(sickbeard.MY_FULLNAME)
        sickbeard.DATA_DIR = sickbeard.PROG_DIR
        sickbeard.MY_ARGS = sys.argv[1:]
        sickbeard.SYS_ENCODING = None

        try:
            locale.setlocale(locale.LC_ALL, "")
            sickbeard.SYS_ENCODING = locale.getpreferredencoding()
        except (locale.Error, IOError):
            pass

        # For OSes that are poorly configured I'll just randomly force UTF-8
        if not sickbeard.SYS_ENCODING or sickbeard.SYS_ENCODING in ('ANSI_X3.4-1968', 'US-ASCII', 'ASCII'):
            sickbeard.SYS_ENCODING = 'UTF-8'

        if not hasattr(sys, "setdefaultencoding"):
            reload(sys)

        if sys.platform == 'win32':
            #pylint: disable=E1101
            if sys.getwindowsversion()[0] >= 6 and sys.stdout.encoding == 'cp65001':
                sickbeard.SYS_ENCODING = 'UTF-8'

        try:
            # pylint: disable=E1101
            # On non-unicode builds this will raise an AttributeError, if encoding type is not valid it throws a LookupError
            sys.setdefaultencoding(sickbeard.SYS_ENCODING)
        except Exception:
            sys.exit("Sorry, you MUST add the SickRage folder to the PYTHONPATH environment variable\n" +
                     "or find another way to force Python to use " + sickbeard.SYS_ENCODING + " for string encoding.")

        # Need console logging for SickBeard.py and SickBeard-console.exe
        self.consoleLogging = (not hasattr(sys, "frozen")) or (sickbeard.MY_NAME.lower().find('-console') > 0)

        # Rename the main thread
        threading.currentThread().name = "MAIN"

        try:
            # pylint: disable=W0612
            opts, args = getopt.getopt(sys.argv[1:], "hqdp::",
                                       ['help', 'quiet', 'nolaunch', 'daemon', 'pidfile=', 'port=',
                                        'datadir=', 'config=', 'noresize'])  # @UnusedVariable
        except getopt.GetoptError:
            sys.exit(self.help_message())

        for o, a in opts:
            # Prints help message
            if o in ('-h', '--help'):
                sys.exit(self.help_message())

            # For now we'll just silence the logging
            if o in ('-q', '--quiet'):
                self.consoleLogging = False

            # Suppress launching web browser
            # Needed for OSes without default browser assigned
            # Prevent duplicate browser window when restarting in the app
            if o in ('--nolaunch',):
                self.noLaunch = True

            # Override default/configured port
            if o in ('-p', '--port'):
                try:
                    self.forcedPort = int(a)
                except ValueError:
                    sys.exit("Port: " + str(a) + " is not a number. Exiting.")

            # Run as a double forked daemon
            if o in ('-d', '--daemon'):
                self.runAsDaemon = True
                # When running as daemon disable consoleLogging and don't start browser
                self.consoleLogging = False
                self.noLaunch = True

                if sys.platform == 'win32' or sys.platform == 'darwin':
                    self.runAsDaemon = False

            # Write a pidfile if requested
            if o in ('--pidfile',):
                self.CREATEPID = True
                self.PIDFILE = str(a)

                # If the pidfile already exists, sickbeard may still be running, so exit
                if os.path.exists(self.PIDFILE):
                    sys.exit("PID file: " + self.PIDFILE + " already exists. Exiting.")

            # Specify folder to load the config file from
            if o in ('--config',):
                sickbeard.CONFIG_FILE = os.path.abspath(a)

            # Specify folder to use as the data dir
            if o in ('--datadir',):
                sickbeard.DATA_DIR = os.path.abspath(a)

            # Prevent resizing of the banner/posters even if PIL is installed
            if o in ('--noresize',):
                sickbeard.NO_RESIZE = True

        # The pidfile is only useful in daemon mode, make sure we can write the file properly
        if self.CREATEPID:
            if self.runAsDaemon:
                pid_dir = os.path.dirname(self.PIDFILE)
                if not os.access(pid_dir, os.F_OK):
                    sys.exit("PID dir: " + pid_dir + " doesn't exist. Exiting.")
                if not os.access(pid_dir, os.W_OK):
                    sys.exit("PID dir: " + pid_dir + " must be writable (write permissions). Exiting.")

            else:
                if self.consoleLogging:
                    sys.stdout.write("Not running in daemon mode. PID file creation disabled.\n")

                self.CREATEPID = False

        # If they don't specify a config file then put it in the data dir
        if not sickbeard.CONFIG_FILE:
            sickbeard.CONFIG_FILE = os.path.join(sickbeard.DATA_DIR, "config.ini")

        # Make sure that we can create the data dir
        if not os.access(sickbeard.DATA_DIR, os.F_OK):
            try:
                os.makedirs(sickbeard.DATA_DIR, 0744)
            except os.error:
                raise SystemExit("Unable to create datadir '" + sickbeard.DATA_DIR + "'")

        # Make sure we can write to the data dir
        if not os.access(sickbeard.DATA_DIR, os.W_OK):
            raise SystemExit("Datadir must be writeable '" + sickbeard.DATA_DIR + "'")

        # Make sure we can write to the config file
        if not os.access(sickbeard.CONFIG_FILE, os.W_OK):
            if os.path.isfile(sickbeard.CONFIG_FILE):
                raise SystemExit("Config file '" + sickbeard.CONFIG_FILE + "' must be writeable.")
            elif not os.access(os.path.dirname(sickbeard.CONFIG_FILE), os.W_OK):
                raise SystemExit(
                    "Config file root dir '" + os.path.dirname(sickbeard.CONFIG_FILE) + "' must be writeable.")

        os.chdir(sickbeard.DATA_DIR)

        # Check if we need to perform a restore first
        restoreDir = os.path.join(sickbeard.DATA_DIR, 'restore')
        if os.path.exists(restoreDir):
            success = self.restoreDB(restoreDir, sickbeard.DATA_DIR)
            if self.consoleLogging:
                sys.stdout.write("Restore: restoring DB and config.ini %s!\n" % ("FAILED", "SUCCESSFUL")[success])

        # Load the config and publish it to the sickbeard package
        if self.consoleLogging and not os.path.isfile(sickbeard.CONFIG_FILE):
            sys.stdout.write("Unable to find '" + sickbeard.CONFIG_FILE + "' , all settings will be default!" + "\n")

        sickbeard.CFG = ConfigObj(sickbeard.CONFIG_FILE)

        # Initialize the config and our threads
        sickbeard.initialize(consoleLogging=self.consoleLogging)

        if self.runAsDaemon:
            self.daemonize()

        # Get PID
        sickbeard.PID = os.getpid()

        # Fix clients old files
        self.fix_clients_nonsense()

        # Build from the DB to start with
        self.loadShowsFromDB()

        if self.forcedPort:
            logger.log(u"Forcing web server to port " + str(self.forcedPort))
            self.startPort = self.forcedPort
        else:
            self.startPort = sickbeard.WEB_PORT

        if sickbeard.WEB_LOG:
            self.log_dir = sickbeard.LOG_DIR
        else:
            self.log_dir = None

        # sickbeard.WEB_HOST is available as a configuration value in various
        # places but is not configurable. It is supported here for historic reasons.
        if sickbeard.WEB_HOST and sickbeard.WEB_HOST != '0.0.0.0':
            self.webhost = sickbeard.WEB_HOST
        else:
            if sickbeard.WEB_IPV6:
                self.webhost = '::'
            else:
                self.webhost = '0.0.0.0'

        # web server options
        self.web_options = {
            'port': int(self.startPort),
            'host': self.webhost,
            'data_root': os.path.join(sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME),
            'web_root': sickbeard.WEB_ROOT,
            'log_dir': self.log_dir,
            'username': sickbeard.WEB_USERNAME,
            'password': sickbeard.WEB_PASSWORD,
            'enable_https': sickbeard.ENABLE_HTTPS,
            'handle_reverse_proxy': sickbeard.HANDLE_REVERSE_PROXY,
            'https_cert': os.path.join(sickbeard.PROG_DIR, sickbeard.HTTPS_CERT),
            'https_key': os.path.join(sickbeard.PROG_DIR, sickbeard.HTTPS_KEY),
        }

        # start web server
        self.webserver = SRWebServer(self.web_options)
        self.webserver.start()

        if self.consoleLogging:
            print "Starting up SickRage " + sickbeard.BRANCH + " from " + sickbeard.CONFIG_FILE

        # Clean up after update
        if sickbeard.GIT_NEWVER:
            toclean = os.path.join(sickbeard.CACHE_DIR, 'mako')
            for root, dirs, files in os.walk(toclean, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            sickbeard.GIT_NEWVER = False

        # Fire up all our threads
        sickbeard.start()

        # Build internal name cache
        name_cache.buildNameCache()

        # Prepopulate network timezones, it isn't thread safe
        network_timezones.update_network_dict()

        # sure, why not?
        if sickbeard.USE_FAILED_DOWNLOADS:
            failed_history.trimHistory()

        # Check for metadata indexer updates for shows (Disabled until we use api)
        #sickbeard.showUpdateScheduler.forceRun()

        # Launch browser
        if sickbeard.LAUNCH_BROWSER and not (self.noLaunch or self.runAsDaemon):
            sickbeard.launchBrowser('https' if sickbeard.ENABLE_HTTPS else 'http', self.startPort, sickbeard.WEB_ROOT)

        # main loop
        while True:
            time.sleep(1)

    def daemonize(self):
        """
        Fork off as a daemon
        """
        # pylint: disable=E1101,W0212
        # Make a non-session-leader child process
        try:
            pid = os.fork()  # @UndefinedVariable - only available in UNIX
            if pid != 0:
                os._exit(0)
        except OSError, e:
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        os.setsid()  # @UndefinedVariable - only available in UNIX

        # https://github.com/SiCKRAGETV/sickrage-issues/issues/2969
        # http://www.microhowto.info/howto/cause_a_process_to_become_a_daemon_in_c.html#idp23920
        # https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch06s08.html
        # Previous code simply set the umask to whatever it was because it was ANDing instead of ORring
        # Daemons traditionally run with umask 0 anyways and this should not have repercussions
        os.umask(0)


        # Make the child a session-leader by detaching from the terminal
        try:
            pid = os.fork()  # @UndefinedVariable - only available in UNIX
            if pid != 0:
                os._exit(0)
        except OSError, e:
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Write pid
        if self.CREATEPID:
            pid = str(os.getpid())
            logger.log(u"Writing PID: " + pid + " to " + str(self.PIDFILE))
            try:
                file(self.PIDFILE, 'w').write("%s\n" % pid)
            except IOError, e:
                logger.log_error_and_exit(
                    u"Unable to write PID file: " + self.PIDFILE + " Error: " + str(e.strerror) + " [" + str(
                        e.errno) + "]")

        # Redirect all output
        sys.stdout.flush()
        sys.stderr.flush()

        devnull = getattr(os, 'devnull', '/dev/null')
        stdin = file(devnull, 'r')
        stdout = file(devnull, 'a+')
        stderr = file(devnull, 'a+')
        os.dup2(stdin.fileno(), sys.stdin.fileno())
        os.dup2(stdout.fileno(), sys.stdout.fileno())
        os.dup2(stderr.fileno(), sys.stderr.fileno())

    @staticmethod
    def remove_pid_file(PIDFILE):
        try:
            if os.path.exists(PIDFILE):
                os.remove(PIDFILE)

        except (IOError, OSError):
            return False

        return True

    @staticmethod
    def loadShowsFromDB():
        """
        Populates the showList with shows from the database
        """

        logger.log(u"Loading initial show list", logger.DEBUG)

        myDB = db.DBConnection()
        sqlResults = myDB.select("SELECT * FROM tv_shows;")

        sickbeard.showList = []
        for sqlShow in sqlResults:
            try:
                curShow = TVShow(int(sqlShow["indexer"]), int(sqlShow["indexer_id"]))
                curShow.nextEpisode()
                sickbeard.showList.append(curShow)
            except Exception, e:
                logger.log(
                    u"There was an error creating the show in " + sqlShow["location"] + ": " + str(e).decode('utf-8'),
                    logger.ERROR)
                logger.log(traceback.format_exc(), logger.DEBUG)

    @staticmethod
    def restoreDB(srcDir, dstDir):
        try:
            filesList = ['sickbeard.db', 'config.ini', 'failed.db', 'cache.db']

            for filename in filesList:
                srcFile = os.path.join(srcDir, filename)
                dstFile = os.path.join(dstDir, filename)
                bakFile = os.path.join(dstDir, '{0}.bak-{1}'.format(filename, datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d_%H%M%S')))
                if os.path.isfile(dstFile):
                    shutil.move(dstFile, bakFile)
                shutil.move(srcFile, dstFile)
            return True
        except Exception:
            return False

    def shutdown(self, event):
        if sickbeard.started:
            # stop all tasks
            sickbeard.halt()

            # save all shows to DB
            sickbeard.saveAll()

            # shutdown web server
            if self.webserver:
                logger.log("Shutting down Tornado")
                self.webserver.shutDown()
                try:
                    self.webserver.join(10)
                except Exception:
                    pass

            # if run as daemon delete the pidfile
            if self.runAsDaemon and self.CREATEPID:
                self.remove_pid_file(self.PIDFILE)

            if event == sickbeard.event_queue.Events.SystemEvent.RESTART:
                install_type = sickbeard.versionCheckScheduler.action.install_type

                popen_list = []

                if install_type in ('git', 'source'):
                    popen_list = [sys.executable, sickbeard.MY_FULLNAME]
                elif install_type == 'win':
                    logger.log(u"You are using a binary Windows build of SickRage. Please switch to using git.", logger.ERROR)

                if popen_list and not sickbeard.NO_RESTART:
                    popen_list += sickbeard.MY_ARGS
                    if '--nolaunch' not in popen_list:
                        popen_list += ['--nolaunch']
                    logger.log(u"Restarting SickRage with " + str(popen_list))
                    logger.shutdown() #shutdown the logger to make sure it's released the logfile BEFORE it restarts SR.
                    subprocess.Popen(popen_list, cwd=os.getcwd())

        # system exit
        logger.shutdown() #Make sure the logger has stopped, just in case
        # pylint: disable=W0212
        os._exit(0)


if __name__ == "__main__":
    # start sickrage
    SickRage().start()
