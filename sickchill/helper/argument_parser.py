import os
import sys
from argparse import ArgumentParser, SUPPRESS


class SickChillArgumentParser:
    def __init__(self, data_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_dir = data_dir
        self.parser = ArgumentParser()

        self.parser.description = """SickChill is an automatic tv library manager. It handles searching, sending to your download client, organizing, renaming,
        and adding images and metadata. It handles it all (with a little bit of magic) so you don't have to.
        (c) 2017 SickChill
        """

        self.parser.add_argument("-q", "--quiet", action="store_true", help="disable logging to the console")
        self.parser.add_argument("--nolaunch", action="store_true", help="suppress launching the web browser on startup")
        self.parser.add_argument("-p", "--port", type=int, help="the port to listen on")
        self.parser.add_argument(
            "--datadir",
            help="full path to a folder where the database, config, cache and log files should be stored. Default: {data_dir}"
            "{sep}".format(data_dir=self.data_dir, sep=os.sep),
        )
        self.parser.add_argument(
            "--config",
            help="full file path to override the default configuration file. Default: {data_dir}{sep}config.ini".format(data_dir=self.data_dir, sep=os.sep),
        )
        self.parser.add_argument("--pidfile", help="combined with --daemon creates a pid file (full path)")
        self.parser.add_argument("--noresize", action="store_true", help="prevent resizing of show images even if PIL is installed")
        daemon_help = "run as daemon (includes options --quiet --nolaunch)"
        if sys.platform in ["win32", "darwin"]:
            daemon_help = "running as daemon is not supported on your platform. it is substituted with: --quiet --nolaunch"
        self.parser.add_argument("-d", "--daemon", action="store_true", help=daemon_help)
        self.parser.add_argument(
            "--force-update",
            action="store_true",
            help="download the latest stable version and force an " "update (use when you're unable to do so using " "the web ui)",
        )

        self.parser.add_argument("--debug", action="store_true", default=False, help=SUPPRESS)
        self.parser.add_argument("--dbdebug", action="store_true", default=False, help=SUPPRESS)
        self.parser.add_argument("--no-file-logging", action="store_true", default=False, help=SUPPRESS)

        self.parser.add_argument("--no-update", action="store_true", help="disable the built-in updater")
        self.parser.add_argument("--flask", action="store_true", help="run the flask server")
        self.parser.add_argument("--flask-host", help="the host for flask listen on", required=False)
        self.parser.add_argument("--flask-port", type=int, help="the port for flask listen on", required=False)

        test_subparser = self.parser.add_subparsers(help="test commands parsers", dest="subparser_name")
        test_name_parser = test_subparser.add_parser("test-name", help="test a release name to see the parse result")
        test_name_parser.add_argument("--name", help="test a release name to see the parse result", required=True)
        test_name_parser.add_argument(
            "--parser",
            help="parser type to use when testing a release name with the parser",
            default="all,normal,anime",
            required=False,
        )

    def parse_args(self, args=None):
        return self.parser.parse_args(args)

    def parse_known_args(self, args=None, namespace=None):
        return self.parser.parse_known_args(args, namespace)
