#!/usr/bin/env python2
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
from __future__ import with_statement

import sys
import shutil

if sys.version_info < (2, 6):
    print "Sorry, requires Python 2.6 or 2.7."
    sys.exit(1)

try:
    import Cheetah

    if Cheetah.Version[0] != '2':
        raise ValueError
except ValueError:
    print "Sorry, requires Python module Cheetah 2.1.0 or newer."
    sys.exit(1)
except:
    print "The Python module Cheetah is required"
    sys.exit(1)

import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'lib')))

# We only need this for compiling an EXE and I will just always do that on 2.6+
if sys.hexversion >= 0x020600F0:
    from multiprocessing import freeze_support  # @UnresolvedImport

import locale
import datetime
import threading
import signal
import traceback
import getopt

import sickbeard

from sickbeard import db
from sickbeard.tv import TVShow
from sickbeard import logger
from sickbeard import webserveInit
from sickbeard.version import SICKBEARD_VERSION
from sickbeard.databases.mainDB import MIN_DB_VERSION
from sickbeard.databases.mainDB import MAX_DB_VERSION

from lib.configobj import ConfigObj
from tornado.ioloop import IOLoop
from daemon import Daemon

signal.signal(signal.SIGINT, sickbeard.sig_handler)
signal.signal(signal.SIGTERM, sickbeard.sig_handler)

throwaway = datetime.datetime.strptime('20110101', '%Y%m%d')

restart = False
daemon = None
startPort = None
forceUpdate = None
noLaunch = None
web_options = None

def loadShowsFromDB():
    """
    Populates the showList with shows from the database
    """

    logger.log(u"Loading initial show list")

    myDB = db.DBConnection()
    sqlResults = myDB.select("SELECT * FROM tv_shows")

    sickbeard.showList = []
    for sqlShow in sqlResults:
        try:
            curShow = TVShow(int(sqlShow["indexer"]), int(sqlShow["indexer_id"]))
            sickbeard.showList.append(curShow)
        except Exception, e:
            logger.log(
                u"There was an error creating the show in " + sqlShow["location"] + ": " + str(e).decode('utf-8'),
                logger.ERROR)
            logger.log(traceback.format_exc(), logger.DEBUG)

            # TODO: update the existing shows if the showlist has something in it

def restore(srcDir, dstDir):
    try:
        for file in os.listdir(srcDir):
            srcFile = os.path.join(srcDir, file)
            dstFile = os.path.join(dstDir, file)
            bakFile = os.path.join(dstDir, file + '.bak')
            shutil.move(dstFile, bakFile)
            shutil.move(srcFile, dstFile)

        os.rmdir(srcDir)
        return True
    except:
        return False

def main():
    """
    TV for me
    """

    global daemon, startPort, forceUpdate, noLaunch, web_options

    # do some preliminary stuff
    sickbeard.MY_FULLNAME = os.path.normpath(os.path.abspath(__file__))
    sickbeard.MY_NAME = os.path.basename(sickbeard.MY_FULLNAME)
    sickbeard.PROG_DIR = os.path.dirname(sickbeard.MY_FULLNAME)
    sickbeard.DATA_DIR = sickbeard.PROG_DIR
    sickbeard.MY_ARGS = sys.argv[1:]
    sickbeard.DAEMON = False
    sickbeard.CREATEPID = False

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

    try:
        # pylint: disable=E1101
        # On non-unicode builds this will raise an AttributeError, if encoding type is not valid it throws a LookupError
        sys.setdefaultencoding(sickbeard.SYS_ENCODING)
    except:
        print 'Sorry, you MUST add the SickRage folder to the PYTHONPATH environment variable'
        print 'or find another way to force Python to use ' + sickbeard.SYS_ENCODING + ' for string encoding.'
        sys.exit(1)

    # Need console logging for SickBeard.py and SickBeard-console.exe
    consoleLogging = (not hasattr(sys, "frozen")) or (sickbeard.MY_NAME.lower().find('-console') > 0)

    # Rename the main thread
    threading.currentThread().name = "MAIN"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "qfdp::",
                                   ['quiet', 'forceupdate', 'daemon', 'port=', 'pidfile=', 'nolaunch', 'config=',
                                    'datadir='])  # @UnusedVariable
    except getopt.GetoptError:
        print "Available Options: --quiet, --forceupdate, --port, --daemon, --pidfile, --config, --datadir"
        sys.exit()

    forceUpdate = False
    forcedPort = None
    noLaunch = False

    for o, a in opts:
        # For now we'll just silence the logging
        if o in ('-q', '--quiet'):
            consoleLogging = False

        # Should we update (from indexer) all shows in the DB right away?
        if o in ('-f', '--forceupdate'):
            forceUpdate = True

        # Suppress launching web browser
        # Needed for OSes without default browser assigned
        # Prevent duplicate browser window when restarting in the app
        if o in ('--nolaunch',):
            noLaunch = True

        # Override default/configured port
        if o in ('-p', '--port'):
            forcedPort = int(a)

        # Run as a double forked daemon
        if o in ('-d', '--daemon'):
            sickbeard.DAEMON = True
            # When running as daemon disable consoleLogging and don't start browser
            consoleLogging = False
            noLaunch = True

            if sys.platform == 'win32':
                sickbeard.DAEMON = False

        # Specify folder to load the config file from
        if o in ('--config',):
            sickbeard.CONFIG_FILE = os.path.abspath(a)

        # Specify folder to use as the data dir
        if o in ('--datadir',):
            sickbeard.DATA_DIR = os.path.abspath(a)

        # Prevent resizing of the banner/posters even if PIL is installed
        if o in ('--noresize',):
            sickbeard.NO_RESIZE = True

        # Write a pidfile if requested
        if o in ('--pidfile',):
            sickbeard.CREATEPID = True
            sickbeard.PIDFILE = str(a)

            # If the pidfile already exists, sickbeard may still be running, so exit
            if os.path.exists(sickbeard.PIDFILE):
                sys.exit("PID file: " + sickbeard.PIDFILE + " already exists. Exiting.")

    # The pidfile is only useful in daemon mode, make sure we can write the file properly
    if sickbeard.CREATEPID:
        if sickbeard.DAEMON:
            pid_dir = os.path.dirname(sickbeard.PIDFILE)
            if not os.access(pid_dir, os.F_OK):
                sys.exit("PID dir: " + pid_dir + " doesn't exist. Exiting.")
            if not os.access(pid_dir, os.W_OK):
                sys.exit("PID dir: " + pid_dir + " must be writable (write permissions). Exiting.")

        else:
            if consoleLogging:
                sys.stdout.write("Not running in daemon mode. PID file creation disabled.\n")

            sickbeard.CREATEPID = False

    # If they don't specify a config file then put it in the data dir
    if not sickbeard.CONFIG_FILE:
        sickbeard.CONFIG_FILE = os.path.join(sickbeard.DATA_DIR, "config.ini")

    # Make sure that we can create the data dir
    if not os.access(sickbeard.DATA_DIR, os.F_OK):
        try:
            os.makedirs(sickbeard.DATA_DIR, 0744)
        except os.error, e:
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

    # Check if we need to perform a restore first
    restoreDir = os.path.join(sickbeard.DATA_DIR, 'restore')
    if os.path.exists(restoreDir):
        if restore(restoreDir, sickbeard.DATA_DIR):
            logger.log(u"Restore successful...")
        else:
            logger.log(u"Restore FAILED!", logger.ERROR)

    os.chdir(sickbeard.DATA_DIR)

    if consoleLogging:
        print "Starting up SickRage " + SICKBEARD_VERSION + " from " + sickbeard.CONFIG_FILE

    # Load the config and publish it to the sickbeard package
    if not os.path.isfile(sickbeard.CONFIG_FILE):
        logger.log(u"Unable to find '" + sickbeard.CONFIG_FILE + "' , all settings will be default!", logger.ERROR)

    sickbeard.CFG = ConfigObj(sickbeard.CONFIG_FILE)

    CUR_DB_VERSION = db.DBConnection().checkDBVersion()

    if CUR_DB_VERSION > 0:
        if CUR_DB_VERSION < MIN_DB_VERSION:
            raise SystemExit("Your database version (" + str(
                CUR_DB_VERSION) + ") is too old to migrate from with this version of SickRage (" + str(
                MIN_DB_VERSION) + ").\n" + \
                             "Upgrade using a previous version of SB first, or start with no database file to begin fresh.")
        if CUR_DB_VERSION > MAX_DB_VERSION:
            raise SystemExit("Your database version (" + str(
                CUR_DB_VERSION) + ") has been incremented past what this version of SickRage supports (" + str(
                MAX_DB_VERSION) + ").\n" + \
                             "If you have used other forks of SB, your database may be unusable due to their modifications.")

    # Initialize the config and our threads
    sickbeard.initialize(consoleLogging=consoleLogging)

    if forcedPort:
        logger.log(u"Forcing web server to port " + str(forcedPort))
        startPort = forcedPort
    else:
        startPort = sickbeard.WEB_PORT

    if sickbeard.WEB_LOG:
        log_dir = sickbeard.LOG_DIR
    else:
        log_dir = None

    # sickbeard.WEB_HOST is available as a configuration value in various
    # places but is not configurable. It is supported here for historic reasons.
    if sickbeard.WEB_HOST and sickbeard.WEB_HOST != '0.0.0.0':
        webhost = sickbeard.WEB_HOST
    else:
        if sickbeard.WEB_IPV6:
            webhost = '::'
        else:
            webhost = '0.0.0.0'

    # web server options
    web_options = {
        'port': int(startPort),
        'host': webhost,
        'data_root': os.path.join(sickbeard.PROG_DIR, 'gui', sickbeard.GUI_NAME),
        'web_root': sickbeard.WEB_ROOT,
        'log_dir': log_dir,
        'username': sickbeard.WEB_USERNAME,
        'password': sickbeard.WEB_PASSWORD,
        'enable_https': sickbeard.ENABLE_HTTPS,
        'handle_reverse_proxy': sickbeard.HANDLE_REVERSE_PROXY,
        'https_cert': sickbeard.HTTPS_CERT,
        'https_key': sickbeard.HTTPS_KEY,
    }

    # Start SickRage
    if daemon and daemon.is_running():
        daemon.restart(daemonize=sickbeard.DAEMON)
    else:
        daemon = SickRage(sickbeard.PIDFILE)
        daemon.start(daemonize=sickbeard.DAEMON)

class SickRage(Daemon):
    def run(self):
        global restart, startPort, forceUpdate, noLaunch, web_options

        # Use this PID for everything
        sickbeard.PID = os.getpid()

        try:
            webserveInit.initWebServer(web_options)
        except IOError:
            logger.log(u"Unable to start web server, is something else running on port %d?" % startPort, logger.ERROR)
            if sickbeard.LAUNCH_BROWSER and not sickbeard.DAEMON:
                logger.log(u"Launching browser and exiting", logger.ERROR)
                sickbeard.launchBrowser(startPort)
            sys.exit()

        # Build from the DB to start with
        loadShowsFromDB()

        # Fire up all our threads
        sickbeard.start()

        # Launch browser if we're supposed to
        if sickbeard.LAUNCH_BROWSER and not noLaunch:
            sickbeard.launchBrowser(startPort)

        # Start an update if we're supposed to
        if forceUpdate or sickbeard.UPDATE_SHOWS_ON_START:
            sickbeard.showUpdateScheduler.action.run(force=True)  # @UndefinedVariable

        if sickbeard.LAUNCH_BROWSER and not (noLaunch or sickbeard.DAEMON or restart):
            sickbeard.launchBrowser(startPort)

        # reset this if sickrage was restarted
        restart = False

        # start IO loop
        IOLoop.current().start()

        # close IO loop
        IOLoop.current().close(True)

        # stop all tasks
        sickbeard.halt()

        # save all shows to DB
        sickbeard.saveAll()

if __name__ == "__main__":
    if sys.hexversion >= 0x020600F0:
        freeze_support()

    while(not sickbeard.shutdown):
        main()

        logger.log("SickRage is restarting, please stand by ...")
        restart = True

    logger.log("Goodbye ...")