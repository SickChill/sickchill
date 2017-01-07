# -*- coding: utf-8 -*
from __future__ import print_function, unicode_literals

import os
import sys
from argparse import ArgumentParser


class SickRageArgumentParser(ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

    def __init__(self, program_dir):
        super(SickRageArgumentParser, self).__init__()
        self.program_dir = program_dir

        self.description = """SickRage is an automatic tv library manager. It handles searching, sending to your download client, organizing, renaming,
        and adding images and metadata. It handles it all (with a little bit of magic) so you don't have to.
        (c) 2017 SickRage
        """

        self.add_argument('-q', '--quiet', action='store_true', help='disable logging to the console')
        self.add_argument('--nolaunch', action='store_true', help='suppress launching the web browser on startup')
        self.add_argument('-p', '--port', type=int, help='the port to listen on')
        self.add_argument('--datadir', help='full path to a folder where the database, config, cache and log files should be stored. Default: {program_dir}'
                                            '{sep}'.format(program_dir=self.program_dir, sep=os.sep))
        self.add_argument('--config', help='full file path to override the default configuration file. Default: {program_dir}{sep}config.ini'.format(
            program_dir=self.program_dir, sep=os.sep))
        self.add_argument('--pidfile', help='combined with --daemon creates a pid file (full path)')
        self.add_argument('--noresize', action='store_true', help='prevent resizing of show images even if PIL is installed')
        daemon_help = 'run as daemon (includes options --quiet --nolaunch)'
        if sys.platform in ['win32', 'darwin']:
            daemon_help = 'running as daemon is not supported on your platform. it is substituted with: --quiet --nolaunch'
        self.add_argument('-d', '--daemon', action='store_true', help=daemon_help)
