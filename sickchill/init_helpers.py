import argparse
import gettext
import logging
import os
import re
import sys
from pathlib import Path
from typing import Union

try:
    from importlib.metadata import Distribution, PackageNotFoundError  # noqa
except ImportError:
    from importlib_metadata import Distribution, PackageNotFoundError  # noqa

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# locale_dir = sickchill_dir / "locale"
pid_file: Path = None


sickchill_dir = Path(__file__).parent
locale_dir = sickchill_dir / "locale"
pyproject_file = sickchill_dir.parent / "pyproject.toml"
git_folder = sickchill_dir.parent / ".git"


def setup_gettext(language: str = None) -> None:
    languages = [language] if language else None
    if not [key for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG") if os.environ.get(key)]:
        os.environ["LC_MESSAGES"] = "en_US.UTF-8"
    gt = gettext.translation("messages", locale_dir, languages=languages, fallback=True)
    gt.install(names=["ngettext"])


def maybe_daemonize():
    """
    Fork off as a daemon
    """
    if sys.platform == "win32":
        return

    args = argparse.ArgumentParser(add_help=False)
    args.add_argument("-d", "--daemon", action="store_true")
    args.add_argument("--pidfile")
    args, extra = args.parse_known_args(sys.argv)

    if not args.daemon:
        return

    global pid_file
    if args.pidfile:
        pid_file = Path(args.pidfile).resolve()

    if pid_file:
        if pid_file.is_file():
            # If the pid file already exists, SickChill may still be running, so exit
            raise SystemExit(f"PID file: {pid_file} already exists. Exiting.")
        pid_dir = pid_file.parent
        if not os.access(pid_dir, os.F_OK):
            raise SystemExit(f"PID dir: {pid_dir} doesn't exist. Exiting.")
        if not os.access(pid_dir, os.W_OK):
            raise SystemExit(f"PID dir: {pid_dir} must be writable (write permissions). Exiting.")

    # Make a non-session-leader child process
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            os._exit(0)  # noqa
    except OSError as error:
        raise SystemExit(f"fork #1 failed: {error}\n")

    os.setsid()  # @UndefinedVariable - only available in UNIX

    # https://github.com/SickChill/SickChill/issues/2969
    # http://www.microhowto.info/howto/cause_a_process_to_become_a_daemon_in_c.html#idp23920
    # https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch06s08.html
    # Previous code simply set the umask to whatever it was because it was ANDing instead of OR-ing
    # Daemons traditionally run with umask 0 anyways and this should not have repercussions
    os.umask(0)

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()
        if pid != 0:
            os._exit(0)  # noqa
    except OSError as error:
        raise SystemExit(f"fork #2 failed: {error}\n")

    # Write pid
    if pid_file:
        pid = os.getpid()

        logger.info(f"Writing PID: {pid} to {pid_file}\n")
        try:
            pid_file.write_text(f"{pid}\n")
        except EnvironmentError as error:
            raise SystemExit(f"Unable to write PID file: {pid_file} Error {error}")

    # Redirect all output
    sys.stdout.flush()
    sys.stderr.flush()

    devnull = getattr(os, "devnull", "/dev/null")
    stdin = open(devnull)
    stdout = open(devnull, "a+")
    stderr = open(devnull, "a+")

    os.dup2(stdin.fileno(), getattr(sys.stdin, "device", sys.stdin).fileno())
    os.dup2(stdout.fileno(), getattr(sys.stdout, "device", sys.stdout).fileno())
    os.dup2(stderr.fileno(), getattr(sys.stderr, "device", sys.stderr).fileno())


def remove_pid_file():
    """
    Remove pid file

    :return:
    """
    try:
        if pid_file and pid_file.exists():
            pid_file.unlink()
    except EnvironmentError:
        pass


def get_distribution() -> Union[Distribution, None]:
    try:
        distribution = Distribution.from_name(__package__)
    except PackageNotFoundError:
        return None

    return distribution


def check_installed() -> bool:
    if pyproject_file.is_file() or git_folder.is_dir():
        return False

    return get_distribution() is not None


def get_current_version() -> str:
    fallback_version = "0.0.0"
    version_regex = re.compile(r'\s*version\s*=\s*["\']([.0-9a-z-+]+)["\']\s*$')
    if pyproject_file.is_file():
        for line in pyproject_file.open():
            match = version_regex.match(line)
            if match:
                return match.group(1)
        return fallback_version

    try:
        return get_distribution().version
    except PackageNotFoundError:
        return fallback_version
