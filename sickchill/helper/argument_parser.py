import os
import sys
from argparse import ArgumentParser, Namespace, SUPPRESS
from pathlib import Path
from typing import Union

from sickchill import settings
from sickchill.helper.common import choose_data_dir
from sickchill.init_helpers import get_current_version, sickchill_dir


def path_dir(path: Union[Path, str]):
    result = Path(path).absolute()

    try:
        result.mkdir(parents=True, exist_ok=True, mode=0o744)
    except PermissionError:
        raise SystemExit(f"Unable to create directory due to permissions: {result}")
    except OSError:
        raise SystemExit(f"Unable to create directory: {result}")

    if not os.access(result, os.W_OK):
        raise SystemExit(f"Directory must be writeable: {result}")

    return result


def path_file(path: Union[Path, str]):
    result = Path(path).absolute()

    path_dir(result.parent)
    return result.absolute()


class SettingsNameSpace:
    def __setattr__(self, key, value):
        key = key.upper()
        if not hasattr(settings, key):
            raise AttributeError(f"Attribute {key} is not in {settings.__name__}")
        setattr(settings, key, value)

    def __getattr__(self, key):
        key = key.upper()
        if not hasattr(settings, key):
            raise AttributeError(f"Attribute {key} is not in {settings.__name__}")
        return getattr(settings, key)


class SickChillArgumentParser(ArgumentParser):
    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(2)

    def __init__(self):
        super().__init__()
        self.data_dir: Path = choose_data_dir(sickchill_dir)

        self.description = """SickChill is an automatic tv library manager. It handles searching, sending to your download client, organizing, renaming,
        and adding images and metadata. It handles it all (with a bit of magic) so you don't have to.
        (c) 2017 SickChill
        """

        self.add_argument("-q", "--quiet", action="store_true", help="disable logging to the console")
        self.add_argument("--nolaunch", action="store_true", help="suppress launching the web browser on startup", dest="no_launch_browser")
        self.add_argument("--host", help="the hostname or ip to bind the tornado server to", dest="web_host", default="0.0.0.0")
        self.add_argument("-p", "--port", type=int, help="the port to listen on", default=8081, dest="web_port")
        self.add_argument("--https", help="use https", action="store_true", dest="enable_https")
        self.add_argument("--ip6", help="use ipv6", action="store_true", dest="web_ipv6")
        self.add_argument("--cert", help="the https certificate to use", dest="https_cert", metavar="CERT")
        self.add_argument("--key", help="the https certificate key to use", dest="https_key", metavar="KEY")
        self.add_argument("--log-web", help="log web information", dest="web_log")

        self.add_argument("--debug", help="enable debug logging", action="store_true", dest="debug")
        self.add_argument("--dbdebug", help="enable database debug logging", action="store_true", dest="dbdebug")

        self.add_argument("--dev", help=SUPPRESS, action="store_true", dest="developer")

        self.add_argument(
            "--datadir",
            dest="data_dir",
            type=path_dir,
            default=self.data_dir,
            help=f"full path to a folder where the database, config, cache and log files should be stored. Default: %(default)s{os.sep}, type %(type)s",
        )
        self.add_argument(
            "--config",
            dest="config_file",
            type=path_file,
            default=self.data_dir.joinpath("config.ini"),
            help=f"full file path to override the default configuration file. Default: %(default)s, type %(type)s",
        )
        self.add_argument("--pidfile", help="combined with --daemon creates a pid file (full path)")
        self.add_argument("--noresize", action="store_true", help="prevent resizing of show images even if PIL is installed", dest="no_resize")
        daemon_help = "run as daemon (includes options --quiet --nolaunch)"
        if sys.platform in ["win32", "darwin"]:
            daemon_help = "running as daemon is not supported on your platform. it is substituted with: --quiet --nolaunch"
        self.add_argument("-d", "--daemon", action="store_true", help=daemon_help)
        self.add_argument(
            "--force-update",
            action="store_true",
            help="download the latest stable version and force an update (use when you're unable to do so using the web ui)",
        )

        self.add_argument("--flask", action="store_true", help="run the flask server")
        self.add_argument("--flask-host", help="the host for flask listen on", required=False)
        self.add_argument("--flask-port", type=int, help="the port for flask listen on", required=False)

        self.add_argument("-v", "--version", action="version", version=f"%(prog)s {get_current_version()}")

    def parse_args(self, args=None, namespace=None) -> Namespace:
        return super().parse_args(args=args, namespace=SettingsNameSpace())
