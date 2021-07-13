#!/usr/bin/env python3

import datetime
import os
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback

import sickchill.start
from sickchill import logger, settings
from sickchill.init_helpers import check_installed, remove_pid_file, setup_gettext
from sickchill.movies import MovieList

setup_gettext()

import mimetypes
from pathlib import Path

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/sfont", ".otf")
mimetypes.add_type("application/sfont", ".ttf")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/font-woff", ".woff")
# Not sure about this one, but we also have halflings in .woff so I think it wont matter
# mimetypes.add_type("application/font-woff2", ".woff2")

from configobj import ConfigObj

from sickchill.helper.argument_parser import SickChillArgumentParser
from sickchill.oldbeard import db, failed_history, name_cache, network_timezones
from sickchill.oldbeard.event_queue import Events
from sickchill.tv import TVShow
from sickchill.update_manager import GitUpdateManager, SourceUpdateManager
from sickchill.views.server_settings import SRWebServer

# http://bugs.python.org/issue7980#msg221094
THROWAWAY = datetime.datetime.strptime("20110101", "%Y%m%d")

signal.signal(signal.SIGINT, sickchill.start.sig_handler)
signal.signal(signal.SIGTERM, sickchill.start.sig_handler)


class SickChill(object):

    """
    Main SickChill module
    """

    def __init__(self):
        # system event callback for shutdown/restart
        settings.events = Events(self.shutdown)

        # daemon constants
        self.run_as_daemon = False

        # web server constants
        self.web_server = None
        self.forced_port = None
        self.no_launch = False

        self.start_port = settings.WEB_PORT

        self.console_logging = True

    @staticmethod
    def clear_cache():
        """
        Remove the Mako cache directory
        """
        try:
            cache_folder = os.path.join(settings.CACHE_DIR, "mako")
            if os.path.isdir(cache_folder):
                shutil.rmtree(cache_folder)
        except Exception:
            logger.warning("Unable to remove the cache/mako directory!")

    def start(self):
        """
        Start SickChill
        """
        # do some preliminary stuff
        settings.MY_FULLNAME = os.path.normpath(os.path.abspath(__file__))
        settings.MY_NAME = os.path.basename(settings.MY_FULLNAME)

        settings.DATA_DIR = os.path.dirname(settings.PROG_DIR)
        profile_path = str(Path.home().joinpath("sickchill").absolute())
        if check_installed():
            settings.DATA_DIR = profile_path

        if settings.DATA_DIR != profile_path:
            checks = ["sickbeard.db", "sickchill.db", "config.ini"]
            if not any([os.path.isfile(os.path.join(settings.DATA_DIR, check)) for check in checks]):
                settings.DATA_DIR = profile_path

        settings.MY_ARGS = sys.argv[1:]

        # Rename the main thread
        threading.currentThread().name = "MAIN"

        args = SickChillArgumentParser(settings.DATA_DIR).parse_args()

        if args.force_update:
            result = self.force_update()
            sys.exit(int(not result))  # Ok -> 0 , Error -> 1

        # Need console logging for SickChill.py and SickChill-console.exe
        settings.NO_RESIZE = args.noresize
        self.console_logging = not (hasattr(sys, "frozen") or args.quiet or args.daemon)
        self.no_launch = args.nolaunch or args.daemon
        self.forced_port = args.port
        self.run_as_daemon = args.daemon and platform.system() != "Windows"

        # The pid file is only useful in daemon mode, make sure we can write the file properly
        if bool(args.pidfile) and not self.run_as_daemon:
            if self.console_logging:
                sys.stdout.write("Not running in daemon mode. PID file creation disabled.\n")

        settings.DATA_DIR = os.path.abspath(args.datadir) if args.datadir else settings.DATA_DIR
        settings.CONFIG_FILE = os.path.abspath(args.config) if args.config else os.path.join(settings.DATA_DIR, "config.ini")

        # Make sure that we can create the data dir
        if not os.access(settings.DATA_DIR, os.F_OK):
            try:
                os.makedirs(settings.DATA_DIR, 0o744)
            except os.error:
                raise SystemExit("Unable to create data directory: {0}".format(settings.DATA_DIR))

        # Make sure we can write to the data dir
        if not os.access(settings.DATA_DIR, os.W_OK):
            raise SystemExit("Data directory must be writeable: {0}".format(settings.DATA_DIR))

        # Make sure we can write to the config file
        if not os.access(settings.CONFIG_FILE, os.W_OK):
            if os.path.isfile(settings.CONFIG_FILE):
                raise SystemExit("Config file must be writeable: {0}".format(settings.CONFIG_FILE))
            elif not os.access(os.path.dirname(settings.CONFIG_FILE), os.W_OK):
                raise SystemExit("Config file root dir must be writeable: {0}".format(os.path.dirname(settings.CONFIG_FILE)))

        os.chdir(settings.DATA_DIR)

        # Check if we need to perform a restore first
        restore_dir = os.path.join(settings.DATA_DIR, "restore")
        if os.path.exists(restore_dir):
            success = self.restore_db(restore_dir, settings.DATA_DIR)
            if self.console_logging:
                sys.stdout.write("Restore: restoring DB and config.ini {0}!\n".format(("FAILED", "SUCCESSFUL")[success]))

        # Load the config and publish it to the oldbeard package
        if self.console_logging and not os.path.isfile(settings.CONFIG_FILE):
            sys.stdout.write("Unable to find {0}, all settings will be default!\n".format(settings.CONFIG_FILE))

        settings.CFG = ConfigObj(settings.CONFIG_FILE, encoding="UTF-8", indent_type="  ")

        # Initialize the config and our threads
        sickchill.start.initialize(consoleLogging=self.console_logging)

        # Get PID
        settings.PID = os.getpid()

        # Build from the DB to start with
        self.load_shows_from_db()

        logger.info("Starting SickChill [{branch}] using '{config}'".format(branch=settings.BRANCH, config=settings.CONFIG_FILE))

        self.clear_cache()

        if settings.DEVELOPER:
            settings.movie_list = MovieList()

        web_options = {}
        if self.forced_port:
            logger.info("Forcing web server to port {port}".format(port=self.forced_port))
            self.start_port = self.forced_port
            web_options.update(
                {
                    "port": int(self.start_port),
                }
            )
        else:
            self.start_port = settings.WEB_PORT

        # start web server
        self.web_server = SRWebServer(web_options)
        self.web_server.start()

        # Fire up all our threads
        sickchill.start.start()

        # Build internal name cache
        name_cache.build_name_cache()

        # Pre-populate network timezones, it isn't thread safe
        network_timezones.update_network_dict()

        # sure, why not?
        if settings.USE_FAILED_DOWNLOADS:
            failed_history.trimHistory()

        # Check for metadata indexer updates for shows (sets the next aired ep!)
        # oldbeard.showUpdateScheduler.forceRun()

        # Launch browser
        if settings.LAUNCH_BROWSER and not self.no_launch:
            sickchill.start.launchBrowser("https" if settings.ENABLE_HTTPS else "http", self.start_port, settings.WEB_ROOT)

        # main loop
        while True:
            time.sleep(1)

    @staticmethod
    def load_shows_from_db():
        """
        Populates the showList with shows from the database
        """
        logger.debug("Loading initial show list")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT indexer, indexer_id, location FROM tv_shows;")

        settings.showList = []
        for sql_show in sql_results:
            try:
                cur_show = TVShow(sql_show["indexer"], sql_show["indexer_id"])
                cur_show.nextEpisode()
                settings.showList.append(cur_show)
            except Exception as error:
                logger.exception("There was an error creating the show in {0}: Error {1}".format(sql_show["location"], error))
                logger.debug(traceback.format_exc())

    @staticmethod
    def restore_db(src_dir, dst_dir):
        """
        Restore the Database from a backup

        :param src_dir: Directory containing backup
        :param dst_dir: Directory to restore to
        :return:
        """
        try:
            files_list = ["sickbeard.db", "sickchill.db", "config.ini", "failed.db", "cache.db"]
            for filename in files_list:
                src_file = os.path.join(src_dir, filename)
                dst_file = os.path.join(dst_dir, filename)
                bak_file = os.path.join(dst_dir, "{0}.bak-{1}".format(filename, datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
                sickchill_db = os.path.join(dst_dir, "sickchill.db")
                sickbeard_db = os.path.join(src_dir, "sickbeard.db")
                if os.path.isfile(src_file):
                    if src_file == sickbeard_db:
                        dst_file = sickchill_db

                    if os.path.isfile(dst_file):
                        shutil.move(dst_file, bak_file)
                    shutil.move(src_file, dst_file)

            sickbeard_db = os.path.join(dst_dir, "sickbeard.db")
            sickchill_db = os.path.join(dst_dir, "sickchill.db")
            if os.path.isfile(sickbeard_db) and not os.path.isfile(sickchill_db):
                shutil.move(sickbeard_db, sickchill_db)

            return True
        except Exception:
            return False

    def shutdown(self, event):
        """
        Shut down SickChill

        :param event: Type of shutdown event, used to see if restart required
        """
        if settings.started:
            sickchill.start.halt()  # stop all tasks
            sickchill.start.saveAll()  # save all shows to DB

            # shutdown web server
            if self.web_server:
                logger.info("Shutting down Tornado")
                self.web_server.shutdown()

                try:
                    self.web_server.join(10)
                except Exception:
                    pass

            self.clear_cache()  # Clean cache

            # if run as daemon delete the pid file
            remove_pid_file()

            if event == sickchill.oldbeard.event_queue.Events.SystemEvent.RESTART:
                popen_list = [sys.executable, settings.MY_FULLNAME]
                if popen_list and not settings.NO_RESTART:
                    popen_list += settings.MY_ARGS
                    if "--nolaunch" not in popen_list:
                        popen_list += ["--nolaunch"]
                    logger.info("Restarting SickChill with {options}".format(options=popen_list))
                    # shutdown the logger to make sure it's released the logfile BEFORE it restarts SC.
                    logger.shutdown()
                    subprocess.Popen(popen_list, cwd=os.getcwd(), universal_newlines=True)

        # Make sure the logger has stopped, just in case
        logger.shutdown()
        os._exit(0)

    @staticmethod
    def force_update():
        """
        Forces SickChill to update to the latest version and exit.

        :return: True if successful, False otherwise
        """

        def update_with_git():
            def run_git(updater, cmd):
                stdout_, stderr_, exit_status = updater._run_git(updater._git_path, cmd)
                if not exit_status == 0:
                    print("Failed to run command: {0} {1}".format(updater._git_path, cmd))
                    return False
                else:
                    return True

            updater = GitUpdateManager()
            if not run_git(updater, "config remote.origin.url https://github.com/SickChill/SickChill.git"):
                return False
            if not run_git(updater, "fetch origin --prune"):
                return False
            if not run_git(updater, "checkout master"):
                return False
            if not run_git(updater, "reset --hard origin/master"):
                return False

            return True

        if os.path.isdir(os.path.join(os.path.dirname(settings.PROG_DIR), ".git")):  # update with git
            print("Forcing SickChill to update using git...")
            result = update_with_git()
            if result:
                print("Successfully updated to latest commit. You may now run SickChill normally.")
                return True
            else:
                print("Error while trying to force an update using git.")

        print("Forcing SickChill to update using source...")
        if not SourceUpdateManager().update():
            print("Failed to force an update.")
            return False

        print("Successfully updated to latest commit. You may now run SickChill normally.")
        return True


if __name__ == "__main__":
    # start SickChill
    SickChill().start()
    remove_pid_file()
