import os
import sys
from argparse import ArgumentParser


class SickChillArgumentParser(ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)

    def __init__(self, data_dir):
        super().__init__()
        self.data_dir = data_dir

        self.description = """SickChill is an automatic tv library manager. It handles searching, sending to your download client, organizing, renaming,
        and adding images and metadata. It handles it all (with a little bit of magic) so you don't have to.
        (c) 2017 SickChill
        """

        self.add_argument("-q", "--quiet", action="store_true", help="disable logging to the console")
        self.add_argument("--nolaunch", action="store_true", help="suppress launching the web browser on startup")
        self.add_argument("-p", "--port", type=int, help="the port to listen on")
        self.add_argument(
            "--datadir",
            help="full path to a folder where the database, config, cache and log files should be stored. Default: {data_dir}"
            "{sep}".format(data_dir=self.data_dir, sep=os.sep),
        )
        self.add_argument(
            "--config",
            help="full file path to override the default configuration file. Default: {data_dir}{sep}config.ini".format(data_dir=self.data_dir, sep=os.sep),
        )
        self.add_argument("--pidfile", help="combined with --daemon creates a pid file (full path)")
        self.add_argument("--noresize", action="store_true", help="prevent resizing of show images even if PIL is installed")
        daemon_help = "run as daemon (includes options --quiet --nolaunch)"
        if sys.platform in ["win32", "darwin"]:
            daemon_help = "running as daemon is not supported on your platform. it is substituted with: --quiet --nolaunch"
        self.add_argument("-d", "--daemon", action="store_true", help=daemon_help)
        self.add_argument(
            "--force-update",
            action="store_true",
            help="download the latest stable version and force an " "update (use when you're unable to do so using " "the web ui)",
        )
