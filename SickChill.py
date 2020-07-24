#!/usr/bin/env python3
# -*- coding: utf-8 -*
# Author: Nic Wolfe <nic@wolfeden.ca>
# URL: http://code.google.com/p/sickbeard/
#
# Rewrite Author: miigotu <miigotu@gmail.com>
# URL: https://sickchill.github.io
#
# This file is part of SickChill.
#
# SickChill is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickChill is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickChill. If not, see <http://www.gnu.org/licenses/>.

# Stdlib Imports
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

# First Party Imports
import sickchill.start
from setup import setup_gettext, setup_lib_path
from sickchill import settings

setup_lib_path()
setup_gettext()

# Stdlib Imports
import mimetypes

mimetypes.add_type("text/css", ".css")
mimetypes.add_type("application/sfont", ".otf")
mimetypes.add_type("application/sfont", ".ttf")
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/font-woff", ".woff")
# Not sure about this one, but we also have halflings in .woff so I think it wont matter
# mimetypes.add_type("application/font-woff2", ".woff2")

# Third Party Imports
from configobj import ConfigObj

# First Party Imports
import sickbeard
from sickbeard import db, failed_history, logger, name_cache, network_timezones
from sickbeard.event_queue import Events
from sickbeard.tv import TVShow
from sickbeard.versionChecker import GitUpdateManager, SourceUpdateManager
from sickchill.helper.argument_parser import SickChillArgumentParser
from sickchill.views.server_settings import SRWebServer

# http://bugs.python.org/issue7980#msg221094
THROWAWAY = datetime.datetime.strptime('20110101', '%Y%m%d')

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
        self.create_pid = False
        self.pid_file = ''

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
            cache_folder = os.path.join(settings.CACHE_DIR, 'mako')
            if os.path.isdir(cache_folder):
                shutil.rmtree(cache_folder)
        except Exception:
            logger.warning('Unable to remove the cache/mako directory!')

    @staticmethod
    def help_message():
        """
        Print help message for commandline options
        """
        help_msg = __doc__
        help_msg = help_msg.replace('SickChill.py', settings.MY_FULLNAME)
        help_msg = help_msg.replace('SickChill directory', settings.PROG_DIR)

        return help_msg

    def start(self):
        """
        Start SickChill
        """
        # do some preliminary stuff
        settings.MY_FULLNAME = os.path.normpath(os.path.abspath(__file__))
        settings.MY_NAME = os.path.basename(settings.MY_FULLNAME)
        settings.PROG_DIR = os.path.dirname(settings.MY_FULLNAME)
        settings.LOCALE_DIR = os.path.join(settings.PROG_DIR, 'locale')
        settings.DATA_DIR = settings.PROG_DIR
        settings.MY_ARGS = sys.argv[1:]

        # Rename the main thread
        threading.currentThread().name = 'MAIN'

        args = SickChillArgumentParser(settings.PROG_DIR).parse_args()

        if args.force_update:
            result = self.force_update()
            sys.exit(int(not result))  # Ok -> 0 , Error -> 1

        # Need console logging for SickChill.py and SickBeard-console.exe
        settings.NO_RESIZE = args.noresize
        self.console_logging = (not hasattr(sys, 'frozen')) or (settings.MY_NAME.lower().find('-console') > 0) and not args.quiet
        self.no_launch = args.nolaunch
        self.forced_port = args.port
        if args.daemon:
            self.run_as_daemon = platform.system() != 'Windows'
            self.console_logging = False
            self.no_launch = True

        self.create_pid = bool(args.pidfile)
        self.pid_file = args.pidfile
        if self.pid_file and os.path.exists(self.pid_file):
            # If the pid file already exists, SickChill may still be running, so exit
            raise SystemExit('PID file: {0} already exists. Exiting.'.format(self.pid_file))

        settings.DATA_DIR = os.path.abspath(args.datadir) if args.datadir else settings.DATA_DIR
        settings.CONFIG_FILE = os.path.abspath(args.config) if args.config else os.path.join(settings.DATA_DIR, 'config.ini')

        # The pid file is only useful in daemon mode, make sure we can write the file properly
        if self.create_pid:
            if self.run_as_daemon:
                pid_dir = os.path.dirname(self.pid_file)
                if not os.access(pid_dir, os.F_OK):
                    sys.exit('PID dir: {0} doesn\'t exist. Exiting.'.format(pid_dir))
                if not os.access(pid_dir, os.W_OK):
                    raise SystemExit('PID dir: {0} must be writable (write permissions). Exiting.'.format(pid_dir))
            else:
                if self.console_logging:
                    sys.stdout.write('Not running in daemon mode. PID file creation disabled.\n')
                self.create_pid = False

        # Make sure that we can create the data dir
        if not os.access(settings.DATA_DIR, os.F_OK):
            try:
                os.makedirs(settings.DATA_DIR, 0o744)
            except os.error:
                raise SystemExit('Unable to create data directory: {0}'.format(settings.DATA_DIR))

        # Make sure we can write to the data dir
        if not os.access(settings.DATA_DIR, os.W_OK):
            raise SystemExit('Data directory must be writeable: {0}'.format(settings.DATA_DIR))

        # Make sure we can write to the config file
        if not os.access(settings.CONFIG_FILE, os.W_OK):
            if os.path.isfile(settings.CONFIG_FILE):
                raise SystemExit('Config file must be writeable: {0}'.format(settings.CONFIG_FILE))
            elif not os.access(os.path.dirname(settings.CONFIG_FILE), os.W_OK):
                raise SystemExit('Config file root dir must be writeable: {0}'.format(os.path.dirname(settings.CONFIG_FILE)))

        os.chdir(settings.DATA_DIR)

        # Check if we need to perform a restore first
        restore_dir = os.path.join(settings.DATA_DIR, 'restore')
        if os.path.exists(restore_dir):
            success = self.restore_db(restore_dir, settings.DATA_DIR)
            if self.console_logging:
                sys.stdout.write('Restore: restoring DB and config.ini {0}!\n'.format(('FAILED', 'SUCCESSFUL')[success]))

        # Load the config and publish it to the sickbeard package
        if self.console_logging and not os.path.isfile(settings.CONFIG_FILE):
            sys.stdout.write('Unable to find {0}, all settings will be default!\n'.format(settings.CONFIG_FILE))

        settings.CFG = ConfigObj(settings.CONFIG_FILE, encoding='UTF-8', indent_type='  ')

        # Initialize the config and our threads
        sickchill.start.initialize(consoleLogging=self.console_logging)

        if self.run_as_daemon:
            self.daemonize()

        # Get PID
        settings.PID = os.getpid()

        # Build from the DB to start with
        self.load_shows_from_db()

        logger.info('Starting SickChill [{branch}] using \'{config}\''.format
                   (branch=settings.BRANCH, config=settings.CONFIG_FILE))

        self.clear_cache()

        web_options = {}
        if self.forced_port:
            logger.info('Forcing web server to port {port}'.format(port=self.forced_port))
            self.start_port = self.forced_port
            web_options.update({
                'port': int(self.start_port),
            })
        else:
            self.start_port = settings.WEB_PORT

        # start web server
        self.web_server = SRWebServer(web_options)
        self.web_server.start()

        # Fire up all our threads
        sickchill.start.start()

        # Build internal name cache
        name_cache.buildNameCache()

        # Pre-populate network timezones, it isn't thread safe
        network_timezones.update_network_dict()

        # sure, why not?
        if settings.USE_FAILED_DOWNLOADS:
            failed_history.trimHistory()

        # Check for metadata indexer updates for shows (sets the next aired ep!)
        # sickbeard.showUpdateScheduler.forceRun()

        # Launch browser
        if settings.LAUNCH_BROWSER and not (self.no_launch or self.run_as_daemon):
            sickchill.start.launchBrowser('https' if settings.ENABLE_HTTPS else 'http', self.start_port, settings.WEB_ROOT)

        # main loop
        while True:
            time.sleep(1)

    def daemonize(self):
        """
        Fork off as a daemon
        """

        # An object is accessed for a non-existent member.
        # Access to a protected member of a client class
        # Make a non-session-leader child process
        try:
            pid = os.fork()  # @UndefinedVariable - only available in UNIX
            if pid != 0:
                os._exit(0)
        except OSError as error:
            sys.stderr.write('fork #1 failed: {error_num}: {error_message}\n'.format
                             (error_num=error.errno, error_message=error.strerror))
            sys.exit(1)

        os.setsid()  # @UndefinedVariable - only available in UNIX

        # https://github.com/SickChill/SickChill/issues/2969
        # http://www.microhowto.info/howto/cause_a_process_to_become_a_daemon_in_c.html#idp23920
        # https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch06s08.html
        # Previous code simply set the umask to whatever it was because it was ANDing instead of OR-ing
        # Daemons traditionally run with umask 0 anyways and this should not have repercussions
        os.umask(0)

        # Make the child a session-leader by detaching from the terminal
        try:
            pid = os.fork()  # @UndefinedVariable - only available in UNIX
            if pid != 0:
                os._exit(0)
        except OSError as error:
            sys.stderr.write('fork #2 failed: Error {error_num}: {error_message}\n'.format
                             (error_num=error.errno, error_message=error.strerror))
            sys.exit(1)

        # Write pid
        if self.create_pid:
            pid = os.getpid()
            logger.info('Writing PID: {pid} to {filename}'.format(pid=pid, filename=self.pid_file))

            try:
                with os.fdopen(os.open(self.pid_file, os.O_CREAT | os.O_WRONLY, 0o644), 'w') as f_pid:
                    f_pid.write('{0}\n'.format(pid))
            except EnvironmentError as error:
                logger.log_error_and_exit('Unable to write PID file: {filename} Error {error_num}: {error_message}'.format
                                          (filename=self.pid_file, error_num=error.errno, error_message=error.strerror))

        # Redirect all output
        sys.stdout.flush()
        sys.stderr.flush()


        devnull = getattr(os, 'devnull', '/dev/null')
        stdin = open(devnull)
        stdout = open(devnull, 'a+')
        stderr = open(devnull, 'a+')

        os.dup2(stdin.fileno(), getattr(sys.stdin, 'device', sys.stdin).fileno())
        os.dup2(stdout.fileno(), getattr(sys.stdout, 'device', sys.stdout).fileno())
        os.dup2(stderr.fileno(), getattr(sys.stderr, 'device', sys.stderr).fileno())

    @staticmethod
    def remove_pid_file(pid_file):
        """
        Remove pid file

        :param pid_file: to remove
        :return:
        """
        try:
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except EnvironmentError:
            return False

        return True

    @staticmethod
    def load_shows_from_db():
        """
        Populates the showList with shows from the database
        """
        logger.debug('Loading initial show list')

        main_db_con = db.DBConnection()
        sql_results = main_db_con.select('SELECT indexer, indexer_id, location FROM tv_shows;')

        settings.showList = []
        for sql_show in sql_results:
            try:
                cur_show = TVShow(sql_show['indexer'], sql_show['indexer_id'])
                cur_show.nextEpisode()
                settings.showList.append(cur_show)
            except Exception as error:
                logger.exception('There was an error creating the show in {0}: Error {1}'.format
                           (sql_show['location'], error))
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
            files_list = ['sickbeard.db', 'config.ini', 'failed.db', 'cache.db']

            for filename in files_list:
                src_file = os.path.join(src_dir, filename)
                dst_file = os.path.join(dst_dir, filename)
                bak_file = os.path.join(dst_dir, '{0}.bak-{1}'.format(filename, datetime.datetime.now().strftime('%Y%m%d_%H%M%S')))
                if os.path.isfile(dst_file):
                    shutil.move(dst_file, bak_file)
                shutil.move(src_file, dst_file)
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
                logger.info('Shutting down Tornado')
                self.web_server.shutdown()

                try:
                    self.web_server.join(10)
                except Exception:
                    pass

            self.clear_cache()  # Clean cache

            # if run as daemon delete the pid file
            if self.run_as_daemon and self.create_pid:
                self.remove_pid_file(self.pid_file)

            if event == sickbeard.event_queue.Events.SystemEvent.RESTART:
                install_type = settings.versionCheckScheduler.action.install_type

                popen_list = []

                if install_type in ('git', 'source'):
                    popen_list = [sys.executable, settings.MY_FULLNAME]
                elif install_type == 'win':
                    logger.exception('You are using a binary Windows build of SickChill. '
                               'Please switch to using git.')

                if popen_list and not settings.NO_RESTART:
                    popen_list += settings.MY_ARGS
                    if '--nolaunch' not in popen_list:
                        popen_list += ['--nolaunch']
                    logger.info('Restarting SickChill with {options}'.format(options=popen_list))
                    # shutdown the logger to make sure it's released the logfile BEFORE it restarts SR.
                    logger.shutdown()
                    subprocess.Popen(popen_list, cwd=os.getcwd())

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
                    print('Failed to run command: {0} {1}'.format(updater._git_path, cmd))
                    return False
                else:
                    return True

            updater = GitUpdateManager()
            if not run_git(updater, 'config remote.origin.url https://github.com/SickChill/SickChill.git'):
                return False
            if not run_git(updater, 'fetch origin --prune'):
                return False
            if not run_git(updater, 'checkout master'):
                return False
            if not run_git(updater, 'reset --hard origin/master'):
                return False

            return True

        if os.path.isdir(os.path.join(settings.PROG_DIR, '.git')):  # update with git
            print('Forcing SickChill to update using git...')
            result = update_with_git()
            if result:
                print('Successfully updated to latest commit. You may now run SickChill normally.')
                return True
            else:
                print('Error while trying to force an update using git.')

        print('Forcing SickChill to update using source...')
        if not SourceUpdateManager().update():
            print('Failed to force an update.')
            return False

        print('Successfully updated to latest commit. You may now run SickChill normally.')
        return True


if __name__ == '__main__':
    # start SickChill
    SickChill().start()
