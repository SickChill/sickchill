import argparse
import gettext
import logging
import os
import re
import site
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Union
from urllib.request import urlopen

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

sickchill_module = Path(__file__).parent.resolve()
pyproject_path = sickchill_module.parent / "pyproject.toml"
# locale_dir = sickchill_dir / "locale"
pid_file: Path = None


def sickchill_dir():
    return os.path.abspath(os.path.dirname(__file__))


def locale_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "locale"))


IS_VIRTUALENV = hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix) or os.getenv("VIRTUAL_ENV")


def setup_gettext(language: str = None) -> None:
    languages = [language] if language else None
    if not [key for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG") if os.environ.get(key)]:
        os.environ["LC_MESSAGES"] = "en_US.UTF-8"
    gt = gettext.translation("messages", locale_dir(), languages=languages, fallback=True)
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
            os._exit(0)
    except OSError as error:
        raise SystemExit(f"fork #1 failed: {error.errno}: {error.strerror}\n")

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
            os._exit(0)
    except OSError as error:
        raise SystemExit(f"fork #2 failed: {error.errno}: {error.strerror}\n")

    # Write pid
    if pid_file:
        pid = os.getpid()

        logger.info(f"Writing PID: {pid} to {pid_file}\n")
        try:
            pid_file.write_text(f"{pid}\n")
        except EnvironmentError as error:
            raise SystemExit(f"Unable to write PID file: {pid_file} Error {error.errno}: {error.strerror}")

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


def check_installed(name: str = __package__) -> bool:
    try:
        from importlib.metadata import Distribution, PackageNotFoundError  # noqa
    except ImportError:
        try:
            from importlib_metadata import Distribution, PackageNotFoundError  # noqa
        except ImportError:
            # Should not get here EVER, but just in case lets just try checking pip freeze instead
            result, output = subprocess.getstatusoutput([f"{sys.executable} -m pip freeze"])
            if result != 0:  # Not Ok
                return False
            is_installed = name in [requirement.split("==")[0] for requirement in output.splitlines()]
            if name != "sickchill" or (name == "sickchill" and is_installed):
                logger.debug(f"{name} installed: {is_installed}")
            return is_installed

    try:
        Distribution.from_name(name)
        logger.debug(f"{name} installed: True")
    except PackageNotFoundError:
        if name != "sickchill":
            logger.debug(f"{name} installed: False")
        return False
    return True


def check_req_installed():
    # get the packages string from poetry
    result, output = subprocess.getstatusoutput(f"cd {pyproject_path.parent} && {sys.executable} -m poetry export -f requirements.txt --without-hashes")

    output = clean_output(output)
    output = output.strip().splitlines()

    # Synology remove existing upto date packages from update lists
    syno_wheelhouse = pyproject_path.parent.with_name("wheelhouse")
    if syno_wheelhouse.is_dir():
        # List installed packages in the freeze format then clean and drop case.
        logger.debug("Synology bypass existing packages: Folder wheelhouse exists")
        result_ins, output_ins = subprocess.getstatusoutput([f"{sys.executable} -m pip list --format freeze"])
        output_ins = output_ins.strip().splitlines()
        output_ins = [s.casefold() for s in output_ins]

        # Add some Python 38 installed packages which SC can't update in DSM
        py38pkg = ["importlib-metadata==", "typing-extensions==", "zipp==3.6.0"]
        output_ins.extend(py38pkg)
        # make the list of packages that need updating by blanking existing ones.
        output_upd = [x for x in output]
        for a in output_ins:
            for b in range(len(output_upd)):
                if output_upd[b].startswith(a):
                    output_upd[b] = ""
        # clean the list up for pip install and send to output.
        output = [x for x in output_upd if x]

    return result, output


def subprocess_call(cmd_list):
    try:
        process = subprocess.Popen(cmd_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, cwd=os.getcwd())
        stdout, stderr = process.communicate()
        process.wait()
        if stdout or stderr:
            logger.info(f"Command result: {stdout or stderr}")
    except Exception as error:
        logger.info(f"Unable to run command: {error}")
        return 126
    return process.returncode


def get_os_id():
    os_release = Path("/etc/os-release").resolve()
    if os_release.is_file():
        from configparser import ConfigParser

        parser = ConfigParser()
        parser.read_string("[DEFAULT]\n" + os_release.read_text())
        try:
            return parser["DEFAULT"]["ID"]
        except (KeyError, IndexError):
            pass


def clean_output(output: str) -> str:
    # clean out Warning line in list (dirty clean)
    # pip lock file warning removal
    output = re.sub(r"Warning.*", "", output)
    # SETUPTOOLS_USE_DISTUTILS=stdlib warnings removal if OS and package cause it
    output = re.sub(r".*warnings\.warn.*", "", output)
    output = re.sub(r".*SetuptoolsDeprecation.*", "", output)
    return output


def pip_install(packages: Union[List[str], str]) -> bool:
    if not isinstance(packages, list):
        packages = clean_output(packages)
        packages = packages.strip().splitlines()

    cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-input",
        "--disable-pip-version-check",
        "--no-python-version-warning",
        "--no-color",
        # "--trusted-host=pypi.org",
        # "--trusted-host=files.pythonhosted.org",
        "-qU",
    ]

    os_id = get_os_id()
    if os_id in ("alpine", "ubuntu"):
        cmd.append(f"--find-links=https://wheel-index.linuxserver.io/{os_id}/")

    if os_id == "alpine":
        cmd.append(f"--extra-index-url=https://alpine-wheels.github.io/index")

    elif os_id in ("raspian", "osmc"):
        cmd.append(f"--extra-index-url=https://www.piwheels.org/simple")

    syno_wheelhouse = pyproject_path.parent.with_name("wheelhouse")
    if syno_wheelhouse.is_dir():
        logger.debug(f"Found wheelhouse dir at {syno_wheelhouse}")
        cmd.append(f"-f{syno_wheelhouse}")

    cmd += packages

    logger.debug(f"pip args: {' '.join(cmd)}")

    result = subprocess_call(cmd)
    if result != 0:  # Not Ok
        logger.info("Trying user site-packages")
        result = subprocess_call(cmd + ["--user"])
        if result != 0:  # Not Ok
            return False
    return True


def check_env_writable():
    """
    Checks if we can install packages to the current environment
    """
    locations = []
    try:
        locations.append(site.getsitepackages()[0])
    except (AttributeError, IndexError):
        try:
            from distutils.sysconfig import get_python_lib

            locations.append(get_python_lib())
        except (ImportError, ModuleNotFoundError):
            pass

        try:
            import pip

            locations.append(str(Path(pip.__path__[0]).parent.resolve()))
        except (ImportError, AttributeError, IndexError):
            pass

    try:
        if site.ENABLE_USER_SITE or site.check_enableusersite():
            if site.USER_SITE:
                locations.append(site.USER_SITE)
            else:
                locations.append(site.getusersitepackages())
    except AttributeError:
        pass

    for location in set(locations):
        logger.debug(f"Can write to {location}: {os.access(location, os.W_OK)}")

    return any([os.access(location, os.W_OK) for location in set(locations)])


def download_to_temp_file(url: str) -> tempfile.NamedTemporaryFile:
    filename = url.rsplit("/", 1)[-1]
    prefix, suffix = filename.rsplit(".", 1)
    tfd = tempfile.NamedTemporaryFile(delete=False, suffix="." + suffix, prefix=prefix, mode="wb")
    tfd.write(urlopen(url).read())
    tfd.close()
    return tfd


def check_and_install_pip() -> None:
    """
    Downloads and runs get-pip.py, installing pip in the current environment
    """

    if not check_installed("pip"):
        logger.info("Installing pip")
        tfd = download_to_temp_file("https://bootstrap.pypa.io/get-pip.py")
        result = subprocess_call([f"{sys.executable}", f"{tfd.name}"])
        if result == 0:
            logger.info("Pip installed")
        else:
            logger.info("There was an error installing pip! Trying user site")
            result = subprocess_call([f"{sys.executable}", f"{tfd.name}", "--user"])
            if result == 0:
                logger.info("Pip installed")
            else:
                logger.info("There was an error installing pip!")

        os.unlink(tfd.name)


def make_virtualenv_and_rerun(location: Path) -> None:
    """
    This is a hail mary, when we cannot install to the already existing virtualenv because
    someone created it as root or another user than the user running this process

    Creates a .venv dir in project root (which is gitignored already)
    if found SC will restart automatically using tthe environment in .venv
    """

    location = location.resolve()
    current_interpreter = Path(sys.executable).resolve()

    result = 0  # Ok
    if str(location) == str(sys.prefix):
        if IS_VIRTUALENV:
            logger.info(f"Unable to install to the existing virtual environment located at {sys.prefix}")
            logger.info("Please check the permissions, and that it does not include global site packages")
        result = 126  # Command invoked cannot execute
    else:
        if not location.is_dir():
            logger.info(f"Because of the above errors, we will try creating a new virtualenvironment in {location}")
            try:
                import venv

                venv.create(location, system_site_packages=False, clear=True, symlinks=os.name != "nt", with_pip=True)
                logger.info(f"Created new virtualenvironment in {location} using venv module!")
            except:
                if check_installed("virtualenv"):
                    result = subprocess_call([f"{sys.executable}", "-m", "virtualenv", "-p", f"{sys.executable}", f"{location}"])
                    if result != 0:  # Not Ok
                        logger.info("Due to the above error, we cannot continue! Exiting")
                    else:
                        logger.info(f"Created new virtualenvironment in {location}")
                else:
                    logger.info("virtualenv module not found, getting a portable one to use temporarily")
                    tfd = download_to_temp_file("https://bootstrap.pypa.io/virtualenv.pyz")
                    result = subprocess_call([f"{sys.executable}", f"{tfd.name}", "-p", f"{sys.executable}", f"{location}"])
                    os.unlink(tfd.name)
                    if result != 0:  # Not Ok
                        logger.info("Due to the above error, we cannot continue! Exiting")
                    else:
                        logger.info(f"Created new virtualenvironment in {location}")

        if location.is_dir() and result == 0:  # Ok
            locations_to_check = []
            # append the bin/python.ext to the new venv path

            check = location
            for part in current_interpreter.parts[-2:]:
                if sys.platform == "win32" and part == "tools":
                    part = "Scripts"
                check /= part
            locations_to_check.append(check)

            locations_to_check.append(location / "bin" / current_interpreter.parts[-1])
            locations_to_check.append(location / "Scripts" / current_interpreter.parts[-1])

            locations_to_check.extend(x for x in location.rglob("*python3.?") if x.is_file())
            locations_to_check.extend(x for x in location.rglob("*python3") if x.is_file())
            locations_to_check.extend(x for x in location.rglob("*python") if x.is_file())

            for place in locations_to_check:
                if place.is_file() and place.stat().st_mode & os.X_OK:
                    # add original arguments to this re-call
                    new_argv = [str(place)] + sys.argv

                    if "VIRTUAL_ENV" not in os.environ:
                        os.environ["VIRTUAL_ENV"] = str(location)

                    logger.info(f"Restarting SickChill with {new_argv}")
                    return os.execvp(new_argv[0], new_argv)

            logger.info(f"Something weird happend when creating the virtualenv, Could not find the bin dir or executable in {location}. Exiting")

    os._exit(result)


def poetry_install() -> None:
    logger.info("Checking poetry")
    if not check_installed():
        if pyproject_path.exists():
            # Check if we can write to this virtualenv
            if not check_env_writable():
                logger.info(f"Current environment is not writable!")
                if not os.access(pyproject_path.parent, os.W_OK):
                    logger.info(f"Source dir is not writable by this user either, we cannot continue: f{pyproject_path.parent}")
                    os._exit(126)

                make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))

            if not IS_VIRTUALENV:
                logger.info(f"We always run from virtualenv when running from source")
                make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))

            check_and_install_pip()

            # Cool, we can write to site-packages
            pip_install(["setuptools", "poetry", "wheel"])
            if check_installed("poetry"):
                logger.debug(f"Poetry installed packages checker started")
                # go check what's already installed and reduce the list for synology.
                result, output = check_req_installed()
                logger.debug(f"Poetry installed packages checker completed")
                if result == 0:  # Ok
                    if output:
                        pip_install(output)
                else:  # Not Ok
                    logger.info(output)
                    make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))
            else:  # Couldn't install poetry, make new venv
                make_virtualenv_and_rerun(pyproject_path.with_name(".venv"))
