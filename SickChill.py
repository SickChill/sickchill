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
from pathlib import Path

import sickchill.start
from sickchill import logger, settings
from sickchill.init_helpers import remove_pid_file, setup_gettext
from sickchill.movies import MovieList

setup_gettext()

import mimetypes

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/sfont", ".otf")
mimetypes.add_type("application/sfont", ".ttf")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/font-woff", ".woff")
# Not sure about this one, but we also have halflings in .woff so I think it wont matter
# mimetypes.add_type("application/font-woff2", ".woff2")

from configobj import ConfigObj

from sickchill.helper.argument_parser import SickChillArgumentParser
from sickchill.oldbeard import db, name_cache, network_timezones
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
        self.no_launch = False

        self.start_port = settings.WEB_PORT

        self.console_logging = True

    @staticmethod
    def clear_cache():
        """
        Remove the Mako cache directory
        """
        try:
            cache_folder = settings.CACHE_DIR / "mako"
            if cache_folder.is_dir():
                shutil.rmtree(cache_folder)
        except Exception:
            logger.warning("Unable to remove the cache/mako directory!")

    def start(self):
        """
        Start SickChill
        """
        # Rename the main thread
        threading.current_thread().name = "MAIN"

        args = SickChillArgumentParser().parse_args()

        if args.force_update:
            result = self.force_update()
            sys.exit(int(not result))  # Ok -> 0 , Error -> 1

        settings.NO_RESIZE = args.noresize
        self.console_logging = not (hasattr(sys, "frozen") or args.quiet or args.daemon)
        self.no_launch = args.nolaunch or args.daemon
        self.run_as_daemon = args.daemon and platform.system() != "Windows"

        # The pid file is only useful in daemon mode, make sure we can write the file properly
        if bool(args.pidfile) and not self.run_as_daemon:
            if self.console_logging:
                sys.stdout.write("Not running in daemon mode. PID file creation disabled.\n")

        settings.DATA_DIR = args.datadir
        settings.CONFIG_FILE = args.config
        assert isinstance(settings.CONFIG_FILE, Path)
        assert os.path.abspath(settings.CONFIG_FILE) == str(settings.CONFIG_FILE)

        # Make sure that we can create the data dir
        if not os.access(settings.DATA_DIR, os.F_OK):
            try:
                os.makedirs(settings.DATA_DIR, 0o744)
            except os.error:
                raise SystemExit(_(f"Unable to create data directory: {settings.DATA_DIR}"))

        # Make sure we can write to the data dir
        if not os.access(settings.DATA_DIR, os.W_OK):
            raise SystemExit(_(f"Data directory must be writeable: {settings.DATA_DIR}"))

        # Make sure we can write to the config file
        if not os.access(settings.CONFIG_FILE, os.W_OK):
            if os.path.isfile(settings.CONFIG_FILE):
                raise SystemExit(_(f"Config file must be writeable: {settings.CONFIG_FILE}"))
                settings.CONFIG_FILE.stat()
            elif not os.access(settings.CONFIG_FILE.parent, os.W_OK):
                raise SystemExit(_(f"Config file parent dir must be writeable: {settings.CONFIG_FILE.parent}"))

        os.chdir(settings.DATA_DIR)

        # Initialize the config and our threads
        sickchill.start.initialize(console_logging=self.console_logging)

        # Build from the DB to start with
        self.load_shows_from_db()

        logger.info(_(f"Starting SickChill [{settings.BRANCH}] using '{settings.CONFIG_FILE}'"))

        self.clear_cache()

        if settings.DEVELOPER:
            settings.movie_list = MovieList()

        if args.port != settings.WEB_PORT:
            logger.info(_(f"Forcing web server to port {args.port}"))

        # start web server
        self.web_server = SRWebServer(args.port)
        self.web_server.start()

        # Fire up all our threads
        sickchill.start.start()

        # Build internal name cache
        name_cache.build_name_cache()

        # Pre-populate network timezones, it isn't thread safe
        network_timezones.update_network_dict()

        # Check for metadata indexer updates for shows (sets the next aired ep!)
        # oldbeard.showUpdateScheduler.forceRun()

        # Launch browser
        if settings.LAUNCH_BROWSER and not self.no_launch:
            sickchill.start.launchBrowser("https" if settings.ENABLE_HTTPS else "http", args.port, settings.WEB_ROOT)

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
                location = sql_show["location"]
                logger.exception(_(f"There was an error creating the show in {location}: Error {error}"))
                logger.debug(traceback.format_exc())


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
                if not settings.NO_RESTART:
                    options = [sys.executable, Path(__file__).absolute()] + sys.argv[1:]
                    if "--nolaunch" not in options:
                        options += ["--nolaunch"]
                    logger.info(_(f"Restarting SickChill with {options}"))
                    # shutdown the logger to make sure it's released the logfile BEFORE it restarts SC.
                    logger.shutdown()
                    subprocess.Popen(options, cwd=os.getcwd(), universal_newlines=True)

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
                    print(f"Failed to run command: {updater._git_path} {cmd}")
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
            print(_("Forcing SickChill to update using git..."))
            result = update_with_git()
            if result:
                print(_("Successfully updated to latest commit. You may now run SickChill normally."))
                return True
            else:
                print(_("Error while trying to force an update using git."))

        print(_("Forcing SickChill to update using source..."))
        if not SourceUpdateManager().update():
            print("Failed to force an update.")
            return False

        print(_("Successfully updated to latest commit. You may now run SickChill normally."))
        return True


def main():
    # start SickChill
    SickChill().start()
    remove_pid_file()


if __name__ == "__main__":
    main()
