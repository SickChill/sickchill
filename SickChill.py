#!/usr/bin/env python3

import datetime
import mimetypes
import os
import platform
import shutil
import signal
import subprocess
import sys
import threading
import time
import traceback
import zipfile
from operator import attrgetter
from pathlib import Path
from typing import List, Union

import sickchill.start

try:
    from frontend.app import FlaskServer
except (ModuleNotFoundError, ImportError):
    FlaskServer = None

from sickchill import logger, settings
from sickchill.helper.common import choose_data_dir
from sickchill.init_helpers import check_installed, get_current_version, remove_pid_file, setup_gettext
from sickchill.movies import MovieList
from sickchill.oldbeard.name_parser.parser import NameParser, ParseResult

setup_gettext()

mimetypes.add_type("text/css", ".css")
# noinspection SpellCheckingInspection
mimetypes.add_type("application/sfont", ".otf")
# noinspection SpellCheckingInspection
mimetypes.add_type("application/sfont", ".ttf")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/font-woff", ".woff")

from configobj import ConfigObj

from sickchill.helper.argument_parser import SickChillArgumentParser
from sickchill.oldbeard import db, name_cache, network_timezones
from sickchill.oldbeard.event_queue import Events
from sickchill.tv import TVShow
from sickchill.update_manager import PipUpdateManager, UpdateManager
from sickchill.views.server_settings import SCWebServer

# http://bugs.python.org/issue7980#msg221094
THROWAWAY = datetime.datetime.strptime("20110101", "%Y%m%d")

signal.signal(signal.SIGINT, sickchill.start.sig_handler)
signal.signal(signal.SIGTERM, sickchill.start.sig_handler)


class SickChill:
    """
    Main SickChill module
    """

    def __init__(self):
        # system event callback for shutdown/restart
        settings.events = Events(self.shutdown)

        # daemon constants
        self.run_as_daemon = False

        # web server constants
        self.flask_server = None

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
        # noinspection PyBroadException
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

        settings.DATA_DIR = choose_data_dir(settings.PROG_DIR)

        settings.MY_ARGS = sys.argv[1:]

        # Rename the main thread
        threading.current_thread().name = "MAIN"

        args = SickChillArgumentParser(settings.DATA_DIR).parse_args()

        # Add methods here when you want to perform an action and exit, without starting the webserver
        if args.subparser_name == "test-name" and args.name:
            results = []
            for parser in args.parser.lower().split(","):
                result = self.test_name(args.name, parser if parser != "all" else "")
                results.append(result)
                parser_name = parser or "all"
                self.log(f"{parser_name}: {result}")
            sys.exit(int(not any(results)))

        if args.no_update:
            settings.DISABLE_UPDATER = True
        elif args.force_update:
            result = self.force_update()
            sys.exit(int(not result))  # Ok -> 0 , Error -> 1
        elif args.install_file:
            result = self.install_file(Path(args.install_file))
            sys.exit(int(not result))  # Ok -> 0 , Error -> 1

        settings.NO_RESIZE = args.noresize
        self.console_logging = not (hasattr(sys, "frozen") or args.quiet or args.daemon)
        self.no_launch = args.nolaunch or args.daemon or args.debug
        self.forced_port = args.port
        self.run_as_daemon = args.daemon and platform.system() != "Windows"

        # The pid file is only useful in daemon mode, make sure we can write the file properly
        if bool(args.pidfile) and not self.run_as_daemon:
            self.log("Not running in daemon mode. PID file creation disabled")

        settings.DATA_DIR = Path(args.datadir).resolve() if args.datadir else settings.DATA_DIR
        settings.CONFIG_FILE = str(Path(args.config).resolve() if args.config else settings.DATA_DIR.joinpath("config.ini"))

        # Make sure that we can create the data dir
        if not os.access(settings.DATA_DIR, os.F_OK):
            try:
                settings.DATA_DIR.mkdir(mode=0x0744, parents=True, exist_ok=True)
            except os.error:
                raise SystemExit("Unable to create data directory: {}".format(settings.DATA_DIR))

        # Make sure we can write to the data dir
        if not os.access(settings.DATA_DIR, os.W_OK):
            raise SystemExit("Data directory must be writeable: {}".format(settings.DATA_DIR))

        # Make sure we can write to the config file
        if not os.access(settings.CONFIG_FILE, os.W_OK):
            if os.path.isfile(settings.CONFIG_FILE):
                raise SystemExit("Config file must be writeable: {}".format(settings.CONFIG_FILE))
            elif not os.access(os.path.dirname(settings.CONFIG_FILE), os.W_OK):
                raise SystemExit("Config file root dir must be writeable: {}".format(os.path.dirname(settings.CONFIG_FILE)))

        os.chdir(settings.DATA_DIR)

        # Check if we need to perform a restore first
        restore_dir = os.path.join(settings.DATA_DIR, "restore")
        if os.path.exists(restore_dir):
            self.log(f"Found restore directory {restore_dir}, restoring your backup!")
            success = self.restore_db(restore_dir, settings.DATA_DIR)
            status = ("FAILED", "SUCCESSFUL")[success]
            self.log(f"Restore: restoring DB and config.ini {status}!", not success)

        upgrade_dir = Path(settings.DATA_DIR) / "force-install"
        if upgrade_dir.is_dir():
            upgrade_files = []
            for upgrade_file in upgrade_dir.glob("sickchill-*-none-any.whl"):
                if upgrade_file.is_file():
                    upgrade_files.append(upgrade_file)

            for upgrade_file in upgrade_dir.glob("Result.zip"):
                if upgrade_file.is_file():
                    upgrade_files.append(upgrade_file)

            if upgrade_files:
                # The only files in here are a wheel and/or a Result.zip
                if len(list(upgrade_dir.iterdir())) == len(upgrade_files):
                    self.log(f"Found force-install directory {upgrade_dir} with {upgrade_files[0].name}, processing")
                    result = self.install_file(upgrade_files[0])
                    self.log(f"Removing sickchill*.whl and Results.zip from force-install directory {upgrade_dir}")
                    for file in upgrade_files:
                        file.unlink()

                    sys.exit(int(not result))  # Ok -> 0 , Error -> 1
                else:
                    self.log(f"Cannot process this upgrade directory, you have files that don't belong in it. Continuing with startup", 1)
                    sys.exit(1)  # Ok -> 0 , Error -> 1

        # Load the config and publish it to the oldbeard package
        if not os.path.isfile(settings.CONFIG_FILE):
            self.log(f"Unable to find {settings.CONFIG_FILE}, all settings will be default!")

        settings.CFG = ConfigObj(settings.CONFIG_FILE, encoding="UTF-8", indent_type="  ")

        # Initialize the config and our threads
        sickchill.start.initialize(
            console_logging=self.console_logging, debug=args.debug, dbdebug=args.dbdebug, disable_file_logging=args.no_file_logging or args.debug
        )

        # Get PID
        settings.PID = os.getpid()

        # Build from the DB to start with
        self.load_shows_from_db()

        logger.info("Starting SickChill [{version}] using '{config}'".format(version=get_current_version(), config=settings.CONFIG_FILE))

        self.clear_cache()

        if settings.DEVELOPER:
            settings.movie_list = MovieList()

        web_options = {"debug": args.debug}
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
        self.web_server = SCWebServer(web_options)
        self.web_server.start()

        if args.flask and FlaskServer:
            # start the flask frontend
            if args.flask_port:
                port = args.flask_port
            else:
                port = int(self.start_port) + 1

            if args.flask_host:
                web_host = args.flask_host
            else:
                if settings.WEB_HOST and settings.WEB_HOST != "0.0.0.0":
                    web_host = settings.WEB_HOST
                else:
                    web_host = ("0.0.0.0", "")[settings.WEB_IPV6]

            self.flask_server = FlaskServer(web_host, port)
            self.flask_server.start()

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
            sickchill.start.launchBrowser("https" if settings.ENABLE_HTTPS else "http", self.start_port, settings.WEB_ROOT)

        # main loop
        while True:
            time.sleep(1)

    @staticmethod
    def load_shows_from_db():
        """
        Populates the show list with shows from the database
        """
        logger.debug("Loading initial show list")

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select("SELECT indexer, indexer_id, location FROM tv_shows;")

        settings.show_list = []
        for sql_show in sql_results:
            if settings.stopping or settings.restarting:
                break

            try:
                cur_show = TVShow(sql_show["indexer"], sql_show["indexer_id"])
                cur_show.next_episode()
                settings.show_list.append(cur_show)
            except Exception as error:
                logger.exception("There was an error creating the show in {}: Error {}".format(sql_show["location"], error))
                logger.debug(traceback.format_exc())
            except KeyboardInterrupt:
                break

        # Presort show_list, so we don't have to do it every page load
        settings.show_list = sorted(settings.show_list, key=attrgetter("sort_name"))

    @staticmethod
    def restore_db(src_dir, dst_dir):
        """
        Restore the Database from a backup

        :param src_dir: Directory containing backup
        :param dst_dir: Directory to restore to
        :return:
        """
        # noinspection PyBroadException
        try:
            files_list = ["sickbeard.db", "sickchill.db", "config.ini", "failed.db", "cache.db"]
            for filename in files_list:
                src_file = os.path.join(src_dir, filename)
                dst_file = os.path.join(dst_dir, filename)
                bak_file = os.path.join(dst_dir, "{}.bak-{}".format(filename, datetime.datetime.now().strftime("%Y%m%d_%H%M%S")))
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
            sickchill.start.save_all()  # save all shows to DB

            # shutdown web server
            if self.web_server:
                logger.info("Shutting down Tornado")
                self.web_server.shutdown()

                # noinspection PyBroadException
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
                    # noinspection SpellCheckingInspection
                    if "--nolaunch" not in popen_list:
                        # noinspection SpellCheckingInspection
                        popen_list += ["--nolaunch"]
                    logger.info("Restarting SickChill with {options}".format(options=popen_list))
                    # shutdown the logger to make sure it's released the logfile BEFORE it restarts SC.
                    logger.shutdown()
                    subprocess.Popen(popen_list, cwd=os.getcwd(), universal_newlines=True)

        # Make sure the logger has stopped, just in case
        logger.shutdown()
        os._exit(0)  # noqa

    def force_update(self):
        """
        Forces SickChill to update to the latest version and exit.

        :return: True if successful, False otherwise
        """
        if not check_installed():
            self.log("Sickchill updater no longer works with git or source installs", 1)
            return False

        self.log("Forcing SickChill to update using pip...")
        if not PipUpdateManager().update():
            self.log("Failed to force an update", 1)
            return False

        self.log("Successfully updated to the latest pip release. You may now run SickChill normally")
        return True

    def install_file(self, file: Path):
        """
        Installs a wheel file, potentially inside a zip file
        :return: True if successful, False otherwise
        """

        if not check_installed():
            self.log("Sickchill updater no longer works with git or source installs", 1)
            return False

        file = file.resolve()

        if not file.is_file():
            self.log(f"File to install was not found ({file})", 1)
            return False

        if file.name.endswith("zip"):
            self.log("File passed with to install was a zip file, extracting the wheel from it")
            if not zipfile.is_zipfile(file):
                self.log("File passed to install is not a valid zip file", 1)
                return False

            try:
                with zipfile.ZipFile(file) as zf:
                    for filename in zf.namelist():
                        if filename.endswith("whl"):
                            extracted = zf.extract(filename, path=file.parent)
                            file = Path(extracted).resolve()
                            break
            except zipfile.BadZipfile as error:
                self.log(f"Error while extracting {file}: {error}", 1)
                return False

        updater = UpdateManager()
        if not updater.updater:
            self.log("Unable to install files, the updater is disabled", 1)
            return False

        self.log(f"Creating a backup of your database and config before installing {file.name}")
        if updater.backup():
            self.log(f"Installing the wheel {file.name}")
            if not updater.updater.pip_install(file):
                self.log(f"Failed to install {file.name}", 1)
                return False
        else:
            self.log("Could not make a backup, not installing the file", 1)
            return False

        self.log("Successfully installed to the wheel. You may now run SickChill normally")
        return True

    @staticmethod
    def test_name(name: str, parse_method="") -> List[Union[ParseResult, None]]:
        return NameParser(parse_method=parse_method)._parse_string(name)

    def log(self, message: str, error: Union[bool, int] = 0) -> None:
        if self.console_logging:
            if error > 0:
                sys.stderr.write(f"{message}\n")
            else:
                sys.stdout.write(f"{message}\n")


def main():
    # start SickChill
    SickChill().start()
    remove_pid_file()


if __name__ == "__main__":
    main()
